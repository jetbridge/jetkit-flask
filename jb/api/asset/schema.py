from marshmallow import fields as f, Schema


class S3PresignedUploadResponse(Schema):
    url = f.String()
    headers = f.Dict()


class UploadRequest(Schema):
    mime_type = f.String(required=True)
    filename = f.String()
