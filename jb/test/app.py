import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from jb.db import db


def create_app(config: dict = {}) -> Flask:
    app = Flask("jb_test")

    # override config for test app
    app.config.update(dict(TESTING=True, SECRET_KEY='testing', **config))

    # jwt initialization
    jwt = JWTManager(app)  # noqa F841

    db.init_app(app)  # init sqlalchemy

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app


@pytest.fixture()
def api_auth(app):
    from jb.api.auth import blp, CoreAuthAPI
    from jb.test.model.user import User
    CoreAuthAPI(auth_model=User)
    app.register_blueprint(blp)


@pytest.fixture()
def api_user(app):
    from jb.api.user import blp, CoreUserAPI
    from jb.test.model.user import User
    CoreUserAPI(user_model=User)
    app.register_blueprint(blp)
