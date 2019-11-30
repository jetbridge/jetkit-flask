from sqlalchemy import Column, DateTime, or_, cast, String, Integer, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Any, Dict
import logging
from flask_sqlalchemy import SQLAlchemy, BaseQuery as FSQLABaseQuery

from jetkit.db.utils import escape_like

log = logging.getLogger(__name__)
TSTZ = DateTime(timezone=True)


class BaseQuery(FSQLABaseQuery):
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


# model mixin
class Upsertable:
    """Model mixin to provide postgres upsert capability."""

    @classmethod
    def upsert_row(
        cls,
        row_class,
        *,
        index_elements: List[str] = None,
        constraint=None,
        set_: Dict[str, Any] = None,
        should_return_result=True,
        values: Dict[str, Any],
    ):
        """Insert, or update if index_elements match.

        :set_: sets values if exists
        :values: are inserted if not exists
        :should_return_result: if false will not return object and will not do commit
        :returns: model fetched from DB.
        """
        # what do we detect conflict on?
        conflict = None
        if index_elements:
            conflict = {"index_elements": index_elements}
        elif constraint:
            conflict = {"constraint": constraint}
        else:
            raise Exception("constraint or index_elements must be specified")

        if not set_:
            set_ = values

        insert_query = (
            pg_insert(row_class)
            .on_conflict_do_update(**conflict, set_=set_)
            .values(**values)
        )
        res = db.session.execute(insert_query)
        if not should_return_result:
            return None
        assert res  # we always get a result if the query completes successfully right?
        db.session.commit()
        id = res.inserted_primary_key[0]
        result = db.session.query(row_class).get(id)
        assert result
        return result
