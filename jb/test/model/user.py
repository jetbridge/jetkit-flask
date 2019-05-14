from jb.model.user import User as CoreUser
from sqlalchemy.orm import relationship


class User(CoreUser):
    __tablename__ = 'person'
    assets = relationship('Asset', back_populates='owner')
