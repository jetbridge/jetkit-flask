from jb.test.model.asset import Asset
from time import sleep
import jb.aws.s3 as jbs3


def test_asset_upsert(s3_client):
    Asset.upsert(s3key="foo/bar")


def test_generate_key(user, session, s3_client):
    session.add(user)
    session.commit()

    key = Asset.generate_key(filename="foo.jpg", prefix="dir")
    assert key.endswith("/foo.jpg")
    assert key.startswith("dir/")

    # same as above
    asset = Asset.upsert_for_filename(filename="foo.jpg", prefix="dir", owner=user)

    asset.object()


def test_asset_generate_presigned_urls(s3_bucket, asset: Asset):
    put = asset.presigned_put(content_type="test/foo")
    assert put.headers["content-type"] == "test/foo"
    assert put.headers["x-amz-acl"] == "private"
    assert put.url

    view = asset.presigned_view_url()
    assert view


def test_upload_trigger(s3_bucket, asset, session):
    session.add(asset)
    session.commit()

    # get url to asset
    direct_url_before = asset.s3_direct_url()

    # create sample upload record for this asset
    test_rec = sample_put_event["Records"][0]
    test_rec["s3"]["bucket"]["name"] = asset.s3bucket
    test_rec["s3"]["object"]["key"] = asset.s3key

    sleep(0.001)  # make updated different from created time

    # process upload event
    asset = Asset.process_s3_create_object_event(test_rec)
    session.commit()
    assert asset
    assert asset.size == test_rec["s3"]["object"]["size"]

    assert (
        asset.s3_direct_url() != direct_url_before
    ), "Direct S3 URL didn't change after upload (for cache busting)"


def test_s3_file_ops(asset: Asset, s3_bucket):
    content = "blah blah"
    key = "testkey.txt"

    # put
    jbs3.put(key=key, content=content)

    # get
    obj = jbs3.get(key=key)
    assert obj["ContentLength"] == len(content)

    # delete
    jbs3.delete(key)


def test_presigned_put_url_without_acl_requires_no_headers(asset: Asset):
    assert len(asset.presigned_put(acl=None).headers) == 0


# sample s3 ObjectCreated:Put event
sample_put_event = {
    "Records": [
        {
            "awsRegion": "eu-central-1",
            "eventName": "ObjectCreated:Put",
            "eventSource": "aws:s3",
            "eventTime": "2019-05-09T16:51:58.123Z",
            "eventVersion": "2.1",
            "requestParameters": {"sourceIPAddress": "93.73.1.1"},
            "responseElements": {
                "x-amz-id-2": "kchrvn7cX3wl3aYAmdPtFuuPaNbkGCiyoy/b7lMOp4V492nijIvdqKGWg7IREdRdqMXP56OE9RQ=",
                "x-amz-request-id": "C3366CADE3F67C90",
            },
            "s3": {
                "bucket": {
                    "arn": "arn:aws:s3:::test-bucket",
                    "name": "test-bucket",  # this is replaced anyway
                    "ownerIdentity": {"principalId": "AI9AWR4T88GZU"},
                },
                "configurationId": "43f7efcf-4d36-4b52-b498-ad629f1c38fa",
                "object": {
                    "eTag": "a2553193ed2a60c59178e37177177f88",
                    "key": "u/mischa/avatar",  # this is replaced too
                    "sequencer": "005CD45AAE0903E030",
                    "size": 1295205,
                },
                "s3SchemaVersion": "1.0",
            },
            "userIdentity": {"principalId": "AWS:AIDAJN6ZTO4AFFSUCKKIE"},
        }
    ]
}
