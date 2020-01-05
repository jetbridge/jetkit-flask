from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Integer, func
import logging
from flask_sqlalchemy import Model as FlaskSQLAModel
from jetkit.db.upsert import Upsertable

if TYPE_CHECKING:
    from jetkit.db.query import BaseQuery

log = logging.getLogger(__name__)

# recommended to use TIMESTAMP WITH TIMEZONE for DateTime columns whenever possible
TSTZ = DateTime(timezone=True)


class BaseModel(FlaskSQLAModel, Upsertable):
    query: "BaseQuery"
    id = Column(Integer, primary_key=True)
    created_at = Column(TSTZ, nullable=False, server_default=func.now())
    updated_at = Column(TSTZ, nullable=True, onupdate=func.now())

    def update(self, **attributes):
        """
        Update object's fields selectively.

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
