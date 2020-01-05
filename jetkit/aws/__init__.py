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
    return bool(os.getenv("AWS_EXECUTION_ENV"))


def get_session():
    """Get boto3 session."""
    session = boto3.session.Session()
    return session
