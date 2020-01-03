from jetkit.db.bases import BaseQueryBase
from jetkit.db.query.filter import FilteredQuery
from jetkit.db.utils import escape_like
from sqlalchemy import Column, or_, cast, String, func


class BaseQuery(FilteredQuery, BaseQueryBase):
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


__all__ = ("BaseQueryBase",)
