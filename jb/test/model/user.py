from jb.model.user import CoreUser
from sqlalchemy.orm import relationship
from jb.db import Model


class User(Model, CoreUser):
    __tablename__ = "test_user"
    assets = relationship("jb.test.model.asset.Asset", back_populates="owner")
