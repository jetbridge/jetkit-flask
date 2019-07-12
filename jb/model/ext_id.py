from sqlalchemy import Column, event, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import DDL


class ExtID:
    """Add an external UUID column.

    Requires "uuid-ossp" extension.
    """

    # UUID that can be used for semi-secret key
    ext_id = Column(
        UUID(as_uuid=True), nullable=False, server_default=text("uuid_generate_v4()")
    )

    @classmethod
    def add_create_uuid_extension_trigger(cls, TableClass):
        """Call this for any tables that use ext_id to ensure they have the uuid-ossp extension already available."""
        trigger = DDL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        event.listen(
            TableClass.__table__,
            "before_create",
            trigger.execute_if(dialect="postgresql"),
        )
