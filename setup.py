from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()

NAME = "jb"
DESCRIPTION = "Common reusable code for python projects."
VERSION = "3.0.0"
REQUIRES_PYTHON = ">=3.6.0"

setup(
    name=NAME,
    version=VERSION,
    python_requires=REQUIRES_PYTHON,
    url="https://github.com/jetbridge/backend-core",
    license="ABRMS",
    author="JetBridge",
    author_email="mischa@jetbridge.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # py_modules=['jb'],
    # if you would be using a package instead use packages instead
    # of py_modules:
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
        "flask-rest-api",
        "Flask-Cors",
        "marshmallow-enum",
        "marshmallow",
    ],
)
