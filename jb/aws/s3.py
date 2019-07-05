"""Interface to Amazon S3."""
import boto3
from flask import current_app
from flask import _app_ctx_stack as stack


def default_bucket():
    """S3 bucket our current_app is configured to use."""
    return current_app.config.get("AWS_S3_BUCKET_NAME")


def upload_file(file_path, content, content_type):
    """Upload file contents to AWS S3.

    :param file_path: name of an uploaded file
    :param content: file content to be uploaded
    :param content_type: mime type of file that should be uploaded
    :returns: S3 key
    """
    s3 = _connect_to_s3()

    s3.put_object(
        Bucket=default_bucket(), Key=file_path, Body=content, ContentType=content_type
    )
    return file_path


def delete_file(key):
    """Delete file from AWS S3."""
    s3 = _connect_to_s3()
    return s3.delete_object(Bucket=default_bucket(), Key=key)


def get_file(file_key, bucket_name=None):
    """Get file contents from AWS S3 by its key.

    :param file_key: key by which a file is stored
    :return A wrapper object over file stored in S3 under specified key
    """
    s3 = _connect_to_s3()

    if not bucket_name:
        bucket_name = default_bucket()

    return s3.get_object(Bucket=bucket_name, Key=file_key)


def get_presigned_view_url(
    bucket, key, content_type="binary/octet-stream", expires_in=86400
):
    """Get pre-signed URL for viewing an S3 object.

    :param bucket: name of an S3 bucket
    :param key: a key to the file
    :param content_type: mime type of the file
    :param expires_in: time (in seconds) for returned URL to be active;
                       optional, by default expires in one day.
    """
    s3 = _connect_to_s3()
    if not bucket:
        bucket = default_bucket()
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key, "ResponseContentType": content_type},
        ExpiresIn=expires_in,
    )

    return url


def get_presigned_put(key, content_type, expires_in=3600 * 6, bucket_name=None):
    """Generate a presigned URL that is good to upload the file key for a short time.

    This returns a full URL with all parameters encoded, unlike get_presigned_upload.
    This is simpler and better, use this instead of get_presigned_upload.

    :returns: url to upload to.
    """
    s3 = _connect_to_s3()
    if not bucket_name:
        bucket_name = default_bucket()
    put_params = dict(Bucket=bucket_name, Key=key, ACL="private")
    if content_type:
        put_params["ContentType"] = content_type
    url = s3.generate_presigned_url(
        ClientMethod="put_object", Params=put_params, ExpiresIn=expires_in
    )
    if current_app.config.get("AWS_S3_ACCELERATION_ENABLED"):
        # override upload URL to use accelerated s3 upload service
        # acceleration MUST be enabled on the s3 bucket!!!!
        # unfortunately there's no (working) way to configure boto to use this
        # see botocore issue #978 on github
        url = url.replace(bucket_name + ".s3", bucket_name + ".s3-accelerate")
    return url


def get_presigned_upload(key, content_type, expires_in=3600 * 6, bucket_name=None):
    """Generate a presigned URL that is good to upload the file key for a short time.

    :deprecated: Use get_presigned_put for new code.
    :returns: url to upload to, fields to send with the request.
    """
    s3 = _connect_to_s3()
    if not bucket_name:
        bucket_name = default_bucket()
    presigned_post = s3.generate_presigned_post(
        Bucket=bucket_name,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[{"Content-Type": content_type}],
        ExpiresIn=expires_in,
    )
    url = presigned_post["url"]
    if current_app.config.get("AWS_S3_ACCELERATION_ENABLED"):
        # override upload URL to use accelerated s3 upload service
        # acceleration MUST be enabled on the s3 bucket!!!!
        # unfortunately there's no (working) way to configure boto to use this
        # see botocore issue #978 on github
        url = url.replace(bucket_name + ".s3", bucket_name + ".s3-accelerate")
    return url, presigned_post["fields"]


def get_asset_url(asset):
    """Get asset pre-signed URL.

    :param asset: Asset wrapper over file stored in S3.
    """
    if asset:
        return get_presigned_view_url(asset.s3bucket, asset.s3key, asset.mime_type)
    else:
        return None


def _connect_to_s3():
    """Get connection to S3 service.

    :return The connection to S3 service
    """
    if stack and stack.top and hasattr(stack.top, "jetbridge_s3_client"):
        return getattr(stack.top, "jetbridge_s3_client")
    session = boto3.session.Session()
    client = session.client(
        "s3",
        aws_access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=current_app.config.get("AWS_ACCESS_KEY_SECRET"),
    )
    if stack and stack.top:
        setattr(stack.top, "jetbridge_s3_client", client)
    return client
