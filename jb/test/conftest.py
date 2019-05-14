from faker import Faker
import pytest
from flask import Flask
from pytest_factoryboy import register
from jb.db.fixture import UserFactory, AssetFactory
from jb.model.user import CoreUserType
from flask_jwt_extended import JWTManager
import os

# for faker
LOCALE = "en_US"

register(UserFactory, "user", user_type=CoreUserType.normal)
register(UserFactory, "admin", user_type=CoreUserType.admin)
register(AssetFactory)


@pytest.fixture(scope='session')
def app():
    """Create a Flask app context for tests."""
    # override config for test app here
    app = Flask("jb_test")
    app.config.update(dict(TESTING=True, OPENAPI_VERSION='3.0.2',
                           OPENAPI_URL_PREFIX='/api',
                           OPENAPI_JSON_PATH='openapi.json',
                           OPENAPI_REDOC_PATH='/doc',
                           OPENAPI_SWAGGER_UI_PATH='/swagger',
                           OPENAPI_SWAGGER_UI_VERSION='3.22.0',
                           API_SPEC_OPTIONS={
                               'components': {
                                   'securitySchemes': {
                                       'bearerAuth': {
                                           'type': 'http',
                                           'scheme': 'bearer',
                                           'bearerFormat': 'JWT'
                                       },
                                   }
                               },
                               'security': [
                                   {
                                       'bearerAuth': []
                                   },
                               ]
                           }))
    # jwt initialization
    jwt = JWTManager(app)  # noqa F841

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'INSECURE')

    from ..views import register_blueprints
    from ..api import api

    api.init_app(app)

    for blp in register_blueprints:
        api.register_blueprint(blp)

    with app.app_context():
        yield app


@pytest.fixture
def session(app, dbsession, engine):
    import jb.model  # noqa: F401
    from jb.db import Base
    Base.metadata.create_all(engine)
    return dbsession


@pytest.fixture
def client_unauthenticated(app):
    # app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def client(app):
    # app.config['TESTING'] = True

    # get flask test client
    client = app.test_client()

    # TODO: generate access token
    access_token = "BOGUS"

    # set environ http header to authenticate user
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"

    return client


@pytest.fixture
def faker():
    return Faker(LOCALE)
