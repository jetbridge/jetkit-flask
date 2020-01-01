from flask import current_app
from sqlalchemy.orm import scoped_session

from jetkit.db.bases import SQLA
from jetkit.db.model import BaseModel
from jetkit.db.query import BaseQuery


# scoped sessionmaker that accesses whatever the current flask-sqlalchemy session is
Session = scoped_session(
    lambda: current_app.extensions["sqlalchemy"].db.session,
    scopefunc=lambda: current_app.extensions["sqlalchemy"].db.session,
)


__all__ = ("BaseQuery", "BaseModel", "SQLA", "Session")
