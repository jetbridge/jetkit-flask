import os

from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayBaseQuery, XRayFlaskSqlAlchemy
from flask_sqlalchemy import BaseQuery as SQLABaseQuery
from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy

# if we are running with AWS-XRay enabled, use the XRay-enhanced versions of query and SQLA for tracing/profiling of queries
xray_enabled = os.getenv("XRAY")

# our base to use for Query classes
BaseQueryBase = XRayBaseQuery if xray_enabled else SQLABaseQuery

# SQLAlchemy base
SQLA = XRayFlaskSqlAlchemy if xray_enabled else FlaskSQLAlchemy

__all__ = ("SQLA", "BaseQueryBase")
