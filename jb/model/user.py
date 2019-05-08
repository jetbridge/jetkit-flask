from enum import Enum, unique
from jb.db import TSTZ, Upsertable, Base
from sqlalchemy import Date, Text, Column
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import relationship


@unique
class UserType(Enum):
    normal = 'normal'
    admin = 'admin'


class User(Base, Upsertable):
    __tablename__ = 'person'  # user is reserved in pg, quoting it is annoying

    email = Column(Text(), unique=True, nullable=True)
    email_validated = Column(TSTZ)

    dob = Column(Date())
    name = Column(Text())

    phone_number = Column(Text())
    _password = Column(Text())

    assets = relationship('Asset', back_populates='createdby')

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


class NormalUser(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.normal,
    }


class AdminUser(User):
    __mapper_args__ = {
        'polymorphic_identity': UserType.admin,
    }
