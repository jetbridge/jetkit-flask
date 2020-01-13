"""Interface to Amazon S3."""
import enum
from typing import Optional

import boto3
from flask import current_app
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Dict


@dataclass_json
@dataclass
class S3PresignedUpload:
    url: str
    headers: Dict[str, str]


@enum.unique
class ACL(enum.Enum):
    """Define who can view this asset.

    Set on S3 object.
    """

    private = "private"
    public_read = "public-read"


class S3MisconfigurationException(Exception):
    pass


def get_default_bucket() -> str:
    if "AWS_S3_BUCKET_NAME" not in current_app.config or not current_app.config.get(
        "AWS_S3_BUCKET_NAME"
    ):
        raise S3MisconfigurationException("AWS_S3_BUCKET_NAME is not defined")
    return current_app.config["AWS_S3_BUCKET_NAME"]


def get_region() -> str:
    session = boto3.session.Session()
    region = session.region_name
    if not region:
        raise S3MisconfigurationException("AWS region not configured")
    return region


def client(region: str = None):
    session = boto3.session.Session()

    # try to determine current region
    region = region or get_region()

    return session.client("s3", endpoint_url=f"https://s3.{region}.amazonaws.com")


def generate_presigned_view_url(bucket: str, key: str, expires_in=86400):
    """Get pre-signed URL for viewing an S3 object.

    :param bucket: name of an S3 bucket
    :param key: a key to the file
    :param expires_in: time (in seconds) for returned URL to be active;
                       optional, by default expires in one day.
    """
    if not bucket:
        bucket = get_default_bucket()
    return client().generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def generate_presigned_put(
    bucket: str,
    key: str,
    content_type: str = None,
    expire: int = 86400,
    acl: Optional[ACL] = ACL.private,
) -> S3PresignedUpload:
    """Generate a presigned URL that can be used to upload a file before the expiration time.

    :returns: An object to return to frontend with URL and headers that should be sent when doing a PUT to S3.
    """
    # PutObject params
    put_params = dict(Bucket=bucket, Key=key)
    headers = {}

    if acl:
        put_params["ACL"] = acl.value
        headers["x-amz-acl"] = acl.value
    if content_type:
        put_params["ContentType"] = content_type
        headers["content-type"] = content_type

    url = client().generate_presigned_url(
        ClientMethod="put_object", Params=put_params, ExpiresIn=expire
    )

    return S3PresignedUpload(url=url, headers=headers)


def put(key: str, content, content_type: str = None, bucket=None):
    """Upload file contents to S3.

    :param content: file content to be uploaded
    :param content_type: mime type of file that should be uploaded
    """
    if not bucket:
        bucket = get_default_bucket()

    req = dict(Bucket=bucket, Key=key, Body=content)

    if content_type:
        req["ContentType"] = content_type

    client().put_object(**req)


def delete(key: str):
    """Delete file from S3."""
    s3 = client()
    return s3.delete_object(Bucket=get_default_bucket(), Key=key)


def get(key: str, bucket: str = None):
    """Get file contents from AWS S3 by its key.

    :param file_key: key by which a file is stored
    :return A wrapper object over file stored in S3 under specified key
    """
    if not bucket:
        bucket = get_default_bucket()

    return client().get_object(Bucket=bucket, Key=key)
