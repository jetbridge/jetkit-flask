from sqlalchemy import Column, DateTime, or_, cast, String, Integer, func
import logging
from flask_sqlalchemy import (
    Model as FlaskSQLAModel,
    SQLAlchemy as FlaskSQLAlchemy,
    BaseQuery as SQLABaseQuery,
)
from aws_xray_sdk.ext.flask_sqlalchemy.query import XRayFlaskSqlAlchemy, XRayBaseQuery
import os

from jetkit.db.utils import escape_like
from jetkit.db.query_filter import FilteredQuery
from jetkit.db.upsert import Upsertable

log = logging.getLogger(__name__)

# recommended to use TIMESTAMP WITH TIMEZONE
TSTZ = DateTime(timezone=True)

# if we are running with AWS-XRay enabled, use the XRay-enhanced versions of query and SQLA for tracing/profiling of queries
xray_enabled = os.getenv("XRAY")
BaseQueryBase = XRayBaseQuery if xray_enabled else SQLABaseQuery
SQLA = XRayFlaskSqlAlchemy if xray_enabled else FlaskSQLAlchemy


class BaseQuery(FilteredQuery):
    def search(self, search_query: str, *columns: Column):
        """Perform a case insensitive search on a set of columns."""
        escape_character = "~"
        search_query = escape_like(search_query, escape_character=escape_character)
        return self.filter(
            or_(
                cast(column, String).ilike(f"%{search_query}%", escape=escape_character)
                for column in columns
            )
        )

    def count_no_subquery(self):
        """Count without doing a subquery.

        See: https://gist.github.com/hest/8798884
        """
        count_q = self.statement.with_only_columns([func.count()]).order_by(None)
        count = self.session.execute(count_q).scalar()
        return count


class BaseModel(FlaskSQLAModel, Upsertable):
    query: BaseQuery
    id = Column(Integer, primary_key=True)
    created_at = Column(TSTZ, nullable=False, server_default=func.now())
    updated_at = Column(TSTZ, nullable=True, onupdate=func.now())

    def update(self, **attributes):
        """
        Selectively update object's fields.

        Can be nested:
            address.update(country={"name": "abc"})
        ...or as a dict:
            address.update(**{"country": {"name": "abc"}})
        """
        self.ensure_valid_attributes(**attributes)

        for field, value in attributes.items():
            if isinstance(value, dict):
                subfield = getattr(self, field)
                if subfield:
                    subfield.update(**value)
            else:
                setattr(self, field, value)

    def ensure_valid_attributes(self, **attributes):
        """
        Ensure that attributes can be used to update values of this model.

        :raises: TypeError if some field is present in `attributes`, but not in this
            model
        :raises: ValueError when attempting to update nested fields of a relationship,
            which is `None` at the moment.

            address.country == None  # True
            address.update(**{"country": {"name": "abc"}}) # raises ValueError

        """
        for field, value in attributes.items():
            if not hasattr(self, field):
                raise TypeError(
                    f"{self.__class__.__name__} doesn't have field '{field}'"
                )
            if isinstance(value, dict):
                subfield = getattr(self, field)
                if not subfield:
                    raise ValueError(
                        f"Tried to assign {value} to fields of {field} field,"
                        f" which is None."
                    )
                subfield.ensure_valid_attributes(**value)
