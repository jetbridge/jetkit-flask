from enum import Enum, unique
from jb.db import TSTZ, Upsertable, Base
from sqlalchemy import Date, Text, Column, Enum as SQLAEnum
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


@unique
class CoreUserType(Enum):
    normal = 'normal'
    admin = 'admin'


class User(Base, Upsertable):
    __abstract__ = True
    __has_assets__ = False  # set to true to enable assets

    # polymorphism
    _user_type = Column(SQLAEnum(CoreUserType), nullable=False, server_default=CoreUserType.normal.value)
    __mapper_args__ = {
        'polymorphic_on': _user_type,
    }

    email = Column(Text(), unique=True, nullable=True)
    email_validated = Column(TSTZ)

    dob = Column(Date())
    name = Column(Text())

    phone_number = Column(Text())
    _password = Column(Text())

    @declared_attr
    def assets(cls):
        """Add asset relationship if it's been enabled."""
        if not cls.__has_assets__:
            return
        return relationship('Asset', back_populates='createdby')

    @hybrid_property
    def password(self):
        return self._password

    @password.setter  # noqa: T484
    def password(self, plaintext):
        self._password = generate_password_hash(plaintext)

    def is_correct_password(self, plaintext):
        return check_password_hash(self._password, plaintext)

    def __repr__(self):
        return f'<User id={self.id} {self.email}>'

    def is_user_type(self, user_type: CoreUserType) -> bool:
        return self._user_type in [user_type, user_type.value]

    def set_user_type(self, user_type: CoreUserType):
        self._user_type = user_type


class NormalUser(User):
    __abstract__ = True
    __mapper_args__ = {
        'polymorphic_identity': CoreUserType.normal,
    }


class AdminUser(User):
    __abstract__ = True
    __mapper_args__ = {
        'polymorphic_identity': CoreUserType.admin,
    }
