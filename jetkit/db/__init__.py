from sqlalchemy import Column, DateTime, or_, cast, String, Integer, func
import logging
from flask_sqlalchemy import SQLAlchemy

from jetkit.db.utils import escape_like
from jetkit.db.query_filter import FilteredQuery

log = logging.getLogger(__name__)
TSTZ = DateTime(timezone=True)


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


class BaseModel:
    query: BaseQuery
    id = Column(Integer, primary_key=True)
    created_at = Column(TSTZ, nullable=False, server_default=func.now())
    updated_at = Column(TSTZ, nullable=True, onupdate=func.now())

    def update(self, **kwargs):
        """Set a dictionary of attributes."""
        for attr, value in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, value)


db = SQLAlchemy(model_class=BaseModel, query_class=BaseQuery)
Model = db.Model
