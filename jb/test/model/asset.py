from jb.model.asset import Asset as CoreAsset
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, ForeignKey, Column
from jb.db import Model


class Asset(Model, CoreAsset):
    __tablename__ = "test_asset"
    user_id = Column(
        Integer,
        ForeignKey("test_user.id", name="owner_user_fk", use_alter=True),
        nullable=True,
    )
    user = relationship(
        "jb.test.model.user.User",
        back_populates="assets",
        foreign_keys=[user_id],
        uselist=False,
    )
