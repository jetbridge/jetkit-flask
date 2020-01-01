from sqlalchemy import Column, DateTime, func
from jetkit.db.query.soft_deletable import SoftDeletableQuery


class SoftDeletable:
    """Model mixin."""

    deleted_at = Column(DateTime(timezone=True))

    def mark_deleted(self) -> None:
        self.deleted_at = func.now()


__all__ = ("SoftDeletableQuery",)
