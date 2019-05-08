from faker import Faker
import pytest
from flask import Flask
from pytest_factoryboy import register
from jb.db.fixture import UserFactory, AssetFactory
from jb.model.user import UserType

# for faker
LOCALE = "en_US"

register(UserFactory, "user", user_type=UserType.normal)
register(UserFactory, "admin", user_type=UserType.admin)
register(AssetFactory)


@pytest.fixture(scope='session')
def app():
    """Create a Flask app context for tests."""
    # override config for test app here
    app = Flask("jb_test")
    app.config.update(dict(TESTING=True, ))

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
