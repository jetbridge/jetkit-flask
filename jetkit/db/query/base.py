import os

from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayBaseQuery
from flask_sqlalchemy import BaseQuery as SQLABaseQuery

xray_enabled = os.getenv("XRAY")

# our base to use for Query classes
BaseQueryBase = XRayBaseQuery if xray_enabled else SQLABaseQuery
