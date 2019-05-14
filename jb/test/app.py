import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

def create_app() -> Flask:
    app = Flask("jb_test")

    # override config for test app
    app.config.update(dict(
        TESTING=True,
        SECRET_KEY='testing'
    ))

    # jwt initialization
    jwt = JWTManager(app)  # noqa F841

    return app


@pytest.fixture(scope='session')
def api_auth(app, sessionmaker):
    from jb.api.auth import blp, CoreAuthAPI
    from jb.test.model.user import User
    CoreAuthAPI(auth_model=User, Session=sessionmaker)
    app.register_blueprint(blp)
