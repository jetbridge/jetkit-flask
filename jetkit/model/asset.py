"""Keep a record in the database of external files."""
import logging
import re
from datetime import datetime
from typing import Optional
from uuid import uuid4
import boto3

from furl import furl
from sqlalchemy import Index, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer, Text

import jetkit.aws.s3 as s3
from jetkit.db import BaseModel
from jetkit.db.upsert import Upsertable
from jetkit.db.extid import ExtID

log = logging.getLogger(__name__)

SLUGIFY_S3_KEY = re.compile(r"[^A-Za-z0-9!\-/_.*'()]")


class Asset(BaseModel, ExtID["Asset"]):
    """Keep a record of files that are stored somewhere.

    You should use S3Asset if you are using S3.
    To ensure the Postgres UUID extension is present, be sure to add `ExtID.add_create_uuid_extension_trigger(Asset)`
    """

    mime_type = Column(Text, nullable=True)
    size = Column(Integer, nullable=True)

    filename = Column(Text, nullable=True)

    @declared_attr
    def owner_id(self):
        return Column(
            Integer,
            ForeignKey("user.id", name="owner_user_fk", use_alter=True),
            nullable=True,
        )

    @declared_attr
    def owner(self):
        return relationship("User", foreign_keys=[self.owner_id], uselist=False)

    @classmethod
    def filter_query_for_user(cls, query, user):
        """List only assets created by user."""
        return query.filter(cls.owner_id == user.id)

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
        return self.check_main_type(expected_type="video")

    def is_image(self):
        """Return true iff asset is image."""
        return self.check_main_type(expected_type="image")

    def is_pdf(self):
        """Return true iff asset is pdf."""
        return self.mime_type == "application/pdf"

    def user_can_read(self, user):
        """Check if a user can view this asset."""
        return user.id == self.owner_id

    def user_can_write(self, user):
        """Asset creator can update asset."""
        return user.id == self.owner_id


class UnknownS3Key(Exception):
    def __init__(self, bucket: str, key: str):
        super().__init__(
            f"Got S3 PutObject event for key `{key}` in `{bucket}` but no matching asset row was found."
        )


class S3Asset(Asset, Upsertable):
    s3bucket = Column(Text, nullable=False)
    s3key = Column(Text, nullable=True)
    region = Column(Text, nullable=False)

    # unique index on bucket/key
    # c.f. https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html
    @declared_attr
    def __table_args__(self):
        return (
            Index(
                f"{self.__tablename__}_asset_s3key_uniq_idx",
                "s3bucket",
                "s3key",
                unique=True,
            ),
        )

    def get_object(self):
        """Get boto3 S3.Object.

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#object
        """
        client = boto3.resource("s3")
        return client.Object(self.s3bucket, self.s3key)

    @classmethod
    def create(
        cls, owner=None, filename: str = None, mime_type: str = None, prefix: str = None
    ) -> "S3Asset":
        if owner:
            assert owner.id
        return cls(  # type: ignore
            region=s3.get_region(),
            s3bucket=s3.get_default_bucket(),
            s3key=cls.generate_key(filename=filename, prefix=prefix),
            filename=filename,
            mime_type=mime_type,
            owner=owner,
        )

    @classmethod
    def upsert(cls, s3key: str, **kwargs) -> "S3Asset":
        # add defaults for region, bucket if not present
        row = super().upsert_row(
            row_class=cls,
            index_elements=["s3bucket", "s3key"],
            values=dict(
                s3key=s3key,
                region=s3.get_region(),
                s3bucket=s3.get_default_bucket(),
                **kwargs,
            ),
        )
        assert row
        return row

    @classmethod
    def upsert_for_filename(
        cls, filename: str = None, prefix: str = None, owner=None, **kwargs
    ) -> "S3Asset":
        s3key = cls.generate_key(filename=filename, prefix=prefix)
        if owner:
            assert owner.id
            kwargs["owner_id"] = owner.id
        return cls.upsert(s3key=s3key, **kwargs)

    @classmethod
    def generate_key(cls, filename: str = None, prefix: str = None) -> str:
        """
        Generate unique (hopefully) s3 key for a given filename.

        E.g. for filename `document.pdf` possible output could be
        `dd01b23cd1f94319b8db8a9628bea792/document.pdf`.
        Slash is included to make filename look better for end-user in browser, as
        browser would suggest saving file as `document.pdf`.

        generate_key(filename='foo.jpg', prefix='avatar') -> 'avatar/123-456-6878/foo.jpg'
        """
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(uuid4().hex)
        if filename:
            parts.append(cls.sanitize_s3_key(filename))
        return "/".join(parts)

    def presigned_view_url(self, **kwargs) -> str:
        """Generate presigned URL to view this asset."""
        return s3.generate_presigned_view_url(
            bucket=self.s3bucket, key=self.s3key, **kwargs
        )

    def _dt(self, dt: datetime) -> str:
        if not dt:
            return "n"
        return str(dt.timestamp())

    def s3_direct_url(self) -> str:
        """Generate S3 URL, assumes this is viewable by the world."""
        lastmod = self.updated_at or self.created_at
        return str(
            furl(
                scheme="https",
                host=f"{self.s3bucket}.s3.{self.region}.amazonaws.com",
                path=f"/{self.s3key}",
                args={"t": self._dt(lastmod)},
            )
        )

    def presigned_put(
        self,
        content_type: str = None,
        expire: int = 86400,
        acl: Optional[s3.ACL] = s3.ACL.private,
    ) -> s3.S3PresignedUpload:
        """Get a S3 presigned URL to upload a file via PUT."""
        return s3.generate_presigned_put(
            content_type=content_type,
            expire=expire,
            acl=acl,
            bucket=self.s3bucket,
            key=self.s3key,
        )

    @classmethod
    def find_by_s3key(cls, s3bucket: str, s3key: str) -> Optional["S3Asset"]:
        return cls.query.filter_by(s3key=s3key, s3bucket=s3bucket).one_or_none()

    @classmethod
    def get_default_bucket(cls) -> str:
        return s3.get_default_bucket()

    @classmethod
    def get_default_region(cls) -> str:
        return s3.get_region()

    @classmethod
    def sanitize_s3_key(cls, key: str) -> str:
        if key in [".", ".."]:
            return ""
        return SLUGIFY_S3_KEY.sub("_", key)

    @classmethod
    def process_s3_create_object_event(cls, record: dict) -> "S3Asset":
        assert "s3" in record

        # look up asset by key/bucket
        s3 = record["s3"]
        s3key = s3["object"]["key"]
        s3bucket = s3["bucket"]["name"]

        # query asset
        asset = cls.query.filter_by(s3key=s3key, s3bucket=s3bucket).one_or_none()
        if not asset:
            raise UnknownS3Key(key=s3key, bucket=s3bucket)

        asset.update_from_upload(s3["object"])
        return asset

    def update_from_upload(self, s3_obj_evt: dict):
        # TODO: save mime type here
        self.size = s3_obj_evt["size"]
        self.updated_at = func.clock_timestamp()
