from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

NAME = "JetKit-Flask"
DESCRIPTION = "Rapid web application development."
VERSION = "8.1.0"
REQUIRES_PYTHON = ">=3.6.0"

setup(
    name=NAME,
    version=VERSION,
    python_requires=REQUIRES_PYTHON,
    url="https://github.com/jetbridge/jetkit-flask",
    license="MIT",
    author="JetBridge",
    author_email="mischa@jetbridge.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["test", "*.test", "*.test.*", "test.*"]),
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    install_requires=[
        "Flask",
        "boto3",
        "dataclasses-json",
        "sqlalchemy",
        "requests",
        "furl",
        "flask-jwt-extended",
        "flask-sqlalchemy",
        "marshmallow-sqlalchemy",
        "flask-smorest",
        "Flask-Cors",
        "marshmallow-enum",
        "marshmallow",
        "aws-xray-sdk",
    ],
)
