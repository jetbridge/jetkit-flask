import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

def create_app() -> Flask:
    app = Flask("jb_test")

    # override config for test app
    app.config.update(dict(TESTING=True,))

    # jwt initialization
    jwt = JWTManager(app)  # noqa F841

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'INSECURE')


@pytest.fixture(scope='session')
def api_auth(app):
    from jb.api.auth import blp
    app.register_blueprint(blp)
