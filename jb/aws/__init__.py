"""Interface to AWS functionality.

Automatically includes access key and other configuration settings from our Flask config.
"""
import boto3
import os


def is_in_aws() -> bool:
    """Check if we're running in AWS.

    If we are, we shouldn't load any extra credentials, region config, etc.

    Vars are: https://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html

    Right now only checks if in Lambda.
    """
    return bool(os.getenv('AWS_EXECUTION_ENV'))


def get_session():
    """Get boto session.

    Don't need to load creds if we're in AWS.
    """
    if is_in_aws():
        return boto3.session.Session()

    from flask import current_app as app
    session = boto3.session.Session(
        aws_access_key_id=app.config.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=app.config.get('AWS_ACCESS_KEY_SECRET'),
        region_name=app.config.get('AWS_DEFAULT_REGION'),
    )
    return session
