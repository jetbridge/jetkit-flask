import warnings
from sqlalchemy import Column, event, text
from sqlalchemy.exc import DataError
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, TypeVar, Generic, Type
from flask_sqlalchemy import Model
from sqlalchemy.schema import DDL

T = TypeVar("T", bound=Model)


class ExtID(Generic[T]):
    """Add an external UUID column `extid`.

    Useful for exposing unique identifiers to clients.
    Requires "uuid-ossp" extension.
    """

    # UUID that can be used for semi-secret key
    extid = Column(
        UUID(as_uuid=True),
        nullable=False,
        server_default=text("uuid_generate_v4()"),
        index=True,
    )

    @classmethod
    def get_by_extid(cls: Type[Model], uuid: str) -> Optional[T]:
        try:
            return cls.query.filter_by(extid=uuid).one_or_none()
        except DataError:  # This means that extid is not a valid uuid
            warnings.warn(f"Attempted to find resource {cls} by invalid extid '{uuid}'")
            return None

    @classmethod
    def get_by_extid_or_404(cls, extid: str) -> Optional[T]:
        obj = cls.get_by_extid(extid)
        if obj is None:
            from flask import abort

            abort(404)
        return obj

    @classmethod
    def add_create_uuid_extension_trigger(cls):
        """Call this for any tables that use ext_id to ensure they have the uuid-ossp extension already available."""
        trigger = DDL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        event.listen(
            cls.__table__, "before_create", trigger.execute_if(dialect="postgresql")
        )
