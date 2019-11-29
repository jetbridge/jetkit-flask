from jetkit.model.user import CoreUser
from sqlalchemy.orm import relationship
from jetkit.db import Model


class User(Model, CoreUser):
    __tablename__ = "test_user"
    assets = relationship("jetkit.test.model.asset.Asset", back_populates="owner")
