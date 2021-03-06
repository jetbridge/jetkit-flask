from sqlalchemy.orm import relationship
from jetkit.model.user import CoreUser
from jetkit.test.app import db
from jetkit.db.soft_deletable import SoftDeletableQuery


class User(db.Model, CoreUser):  # type: ignore
    __tablename__ = "test_user"
    query_class = SoftDeletableQuery
    assets = relationship("jetkit.test.model.asset.Asset", back_populates="owner")


User.add_create_uuid_extension_trigger()
