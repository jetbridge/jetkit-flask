"""Asset model - files stored on AWS S3."""
import base64
import enum

import boto3
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, Text
from flask import current_app
import jb.aws.s3 as s3
import hashlib
import os.path
import mimetypes
import random
import re
import logging
import botocore.exceptions
from furl import furl
from jb.db import db, BaseModel

log = logging.getLogger(__name__)


class AssetStatus(enum.Enum):
    added = 'added'
    in_progress = 'in_progress'
    completed = 'completed'
    errored = 'errored'


class Asset(BaseModel):
    """Keep a record of files that have been uploaded to S3."""
    s3bucket = Column(Text, nullable=False)
    s3key = Column(Text, nullable=False)

    mime_type = Column(Text, nullable=False)
    size = Column(Integer, nullable=True)

    filename = Column(Text, nullable=True)

    views = Column(Integer, nullable=False, server_default='0')

    def check_main_type(self, expected_type):
        """Check if main mime type is equal to expected type."""
        if not self.mime_type:
            return False
        mimetype_parts = self.mime_type.split("/")
        if mimetype_parts:
            return mimetype_parts[0] == expected_type
        return False

    def is_video(self):
        """Return true iff asset is video."""
        return self.check_main_type(expected_type='video')

    def is_image(self):
        """Return true iff asset is image."""
        return self.check_main_type(expected_type='image')

    def is_pdf(self):
        """Return true iff asset is pdf."""
        return self.mime_type == 'application/pdf'

    def user_can_read(self, user):
        """Check if a user can view this asset.

        Make sure this is implemented properly for all possible asset types so that
        people cannot enumerate assets.
        """
        # more cases go here...
        if not user:  # anonymous user
            # can access asset unowned asset from public bucket
            return self.s3bucket in current_app.config.get('S3_PUBLIC_BUCKETS', []) and self.createdby_user_id is None
        return user.id == self.createdby_user_id

    def user_can_write(self, user):
        """Asset creator can update asset."""
        return user.id == self.createdby_user_id

    @classmethod
    def filter_query_for_user(cls, query, user):
        """List only assets created by user."""
        return query.filter(Asset.createdby_user_id == user.id)

    def base64_encoded_external_link(self):
        """Return base64 encoded external link."""
        external_link = self.external_link()
        return base64.b64encode(external_link.encode()).decode()

    def external_link(self, email=None):
        """Return external link to access this asset."""
        return self.s3_view_url()

    def s3_view_url(self):
        """Generate presigned URL to view this asset."""
        assert self.s3bucket, "s3_view_url() called on asset with no s3bucket set"
        assert self.s3key, "s3_view_url() called on asset with no s3key set"
        extra = {}
        if self.mime_type:
            extra['content_type'] = self.mime_type
        return s3.get_presigned_view_url(self.s3bucket, self.s3key, **extra)

    def s3_direct_url(self):
        """Generate S3 URL, assumes this is viewable by the world."""
        lastmod = self.updated if self.updated else self.created
        return furl(
            scheme="https",
            host=f"{self.s3bucket}.s3.{self.region}.amazonaws.com",
            path=f"/{self.s3key}",
            args={"t": self._dt(lastmod)},
        )

    def generate_presigned_upload(
        self, content_type: str = None, expire: int = 86400, acl: s3.ACL = s3.ACL.private
    ):
        """Get a S3 presigned URL to upload a file via PUT."""
        headers = {"x-amz-acl": acl.value}

        # PutObject params
        put_params = dict(Bucket=self.s3bucket, Key=self.s3key, ACL=acl.value)
        if content_type:
            put_params["ContentType"] = content_type
            headers["content-type"] = content_type

        s3 = boto3.client(
            "s3", endpoint_url=f"https://s3.{self.region}.amazonaws.com"
        )
        url = s3.generate_presigned_url(
            ClientMethod="put_object", Params=put_params, ExpiresIn=expire
        )
        return {"url": url, "headers": headers}

    @classmethod
    def _generate_s3_key(cls, directory, file_name, content_type):
        """Hash everything together and hope we get a unique S3key."""
        assert directory

        h = hashlib.sha256()
        h.update(str(random.random()).encode('utf-8'))  # bleh
        h.update(current_app.config['SECRET_KEY'].encode('utf-8'))

        key_name = "{}_original".format(h.hexdigest())

        # add extension to our keyname if we got it
        extension = None
        if file_name:
            # use uploaded file extension
            extension = os.path.splitext(file_name)[1]
            # slugify name and prefix it
            file_name_slug = re.sub(r'[^A-Za-z0-9]', '-', file_name)
            key_name = file_name_slug + "_" + key_name
        if not extension and content_type:
            # or try to guess from mime type
            extension = mimetypes.guess_extension(content_type)
        if extension:
            key_name = key_name + extension

        key_path = os.path.join(directory, key_name)

        # make sure this key is unique (it really really should be)
        existing_asset = cls.query.filter_by(s3key=key_path).one_or_none()
        assert not existing_asset, "got highly unexpected s3 key collision!"
        return key_path

    @classmethod
    def get_asset_put_url(cls, directory, file_name, content_type, bucket_name=None):
        """Generate presigned S3 upload URL.

        :returns: URL, s3key
        """
        s3key = cls._generate_s3_key(directory, file_name, content_type)
        url = s3.get_presigned_put(s3key, content_type, bucket_name=bucket_name)
        return url, s3key

    @classmethod
    def create_asset_from_flask_upload(cls, directory, upload, owner):
        """Copy file to S3 and return asset."""
        assert directory
        assert upload
        assert owner
        content_type = upload.mimetype
        content = upload.read()
        file_name = upload.filename
        s3key = cls._generate_s3_key(directory, file_name, content_type)
        s3key = s3.upload_file(
            s3key,
            content,
            content_type=content_type,
        )
        asset = cls.create_asset(s3key, content_type, owner, file_name)
        return asset

    @classmethod
    def create_from_content(cls, *, user, content, content_type, directory=None, s3key: str=None, acl: s3.ACL = s3.ACL.private):
        """Copy file to S3 and return asset."""
        # get S3 key
        if not s3key:
            s3key = cls._generate_s3_key(directory=directory, file_name='raw', content_type=content_type)
        # upload to S3
        s3key = s3.upload_file(
            s3key,
            content,
            content_type=content_type,
            acl=acl,
        )
        # create asset row
        asset = cls.create_asset(s3key=s3key, content_type=content_type, status='completed', owner=user)
        return asset

    @classmethod
    def create_asset(cls, s3key, content_type, owner=None, filename=None, status=None, bucket_name=None):
        """Create an asset record for an S3 file.

        :param s3key: s3key which may or may not really exist, depending on status.
        :owner: User that owns this asset.
        :content_type: MIME type.
        :filename: File name of the asset.
        :status: This asset may be pending upload to S3 or may refer to a real file.
        :bucket_name: Optional
        :returns: asset.
        """
        if not bucket_name:
            bucket_name = s3.default_bucket()

        # check for existing asset with the same s3key
        asset: Asset = Asset.query.filter_by(s3key=s3key, s3bucket=bucket_name).one_or_none()

        # validate that this key really points to a file in s3
        content_length = None
        if status != 'added':
            try:
                s3_file = s3.get_file(s3key, bucket_name=bucket_name)
                content_length = s3_file['ContentLength']
            except botocore.exceptions.ClientError as e:
                # file doesn't exist (most likely)
                log.error("Got create_asset() call for invalid S3 key {}".format(s3key))
                log.exception(e)
                raise ValueError("S3 key is not valid")

        # upsert
        if asset:
            if asset.createdby_user_id != owner.id:
                # ruh roh
                log.error("{} tried to upload an asset with the same S3 key as an asset owned by {}".format(
                    owner, asset.createdby))
                raise ValueError("S3 key is not unique")
            # ok let's update the asset
            asset.mime_type = content_type
            asset.size = content_length
            asset.s3bucket = bucket_name
        else:
            # ok let's create the asset
            asset = Asset(
                createdby_user_id=owner.id if owner else None,
                s3bucket=bucket_name,
                s3key=s3key,
                mime_type=content_type,
                views=0,
                filename=filename,
                size=content_length,
            )
            if status:
                asset.status = status
            db.session.add(asset)

        db.session.commit()
        return asset

    def get_hash(self) -> str:
        """Get security hash for preventing enumeration."""
        m = hashlib.sha256()
        m.update(current_app.config['SECRET_KEY'].encode('utf-8'))
        m.update(str(self.id).encode("utf-8"))
        hex_ = m.hexdigest()
        return hex_

    def file_name_without_type(self):
        """Return file name without type."""
        parts = self.filename.split('.') if self.filename else []
        if parts:
            return ".".join(parts)

    @classmethod
    def get_asset(cls, asset_id, asset_hash):
        """Return asset by id validating with the hash."""
        asset = cls.query.get(asset_id)
        if not asset:
            log.warning(f"Got invalid asset ID in view endpoint, id={asset_id} hash={asset_hash}")
            return None
        if asset.get_hash() != asset_hash:
            log.info(f"Asset security hash does not match, id={asset_id}, hash={asset_hash}")
            return None
        return asset
