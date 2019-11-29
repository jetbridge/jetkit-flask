from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from jetkit.db import Model
from jetkit.model.asset import S3Asset as CoreAsset


class Asset(Model, CoreAsset):
    __tablename__ = "test_asset"
    owner_id = Column(
        Integer,
        ForeignKey("test_user.id", name="owner_user_fk", use_alter=True),
        nullable=True,
    )
    owner = relationship(
        "jetkit.test.model.user.User",
        back_populates="assets",
        foreign_keys=[owner_id],
        uselist=False,
    )


Asset.add_create_uuid_extension_trigger()
