from jb.model.asset import Asset as CoreAsset
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, ForeignKey, Column


class Asset(CoreAsset):
    __tablename__ = 'asset'
    owner_id = Column(Integer, ForeignKey('user.id', name="owner_user_fk", use_alter=True), nullable=True)
    owner = relationship('jb.test.model.user.User', back_populates='assets', foreign_keys=[owner_id], uselist=False)
