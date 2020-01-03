from typing import TYPE_CHECKING

from jetkit.db.query.filter import QueryFilter, FilteredQuery

if TYPE_CHECKING:
    from jetkit.db.soft_deletable import SoftDeletable


class SoftDeletableQueryFilter(QueryFilter):
    """Omit rows marked as deleted."""

    def apply_default_filter(self) -> "SoftDeletableQueryFilter":
        assert isinstance(self, QueryFilter)
        return self.filter(self.entity.deleted_at.is_(None))

    def get_filter(self, obj: "SoftDeletable") -> bool:
        return obj is None or not obj.deleted_at


class SoftDeletableQuery(FilteredQuery):
    """Query mixin."""

    default_filters = [SoftDeletableQueryFilter]
