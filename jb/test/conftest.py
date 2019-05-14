from faker import Faker
import pytest
from pytest_factoryboy import register
from jb.db.fixture import UserFactory, AssetFactory
from jb.model.user import CoreUserType
import os
from jb.test.app import create_app, api_auth
from sqlalchemy.orm import sessionmaker as sqla_sessionmaker


# for faker
LOCALE = "en_US"

register(UserFactory, "user", user_type=CoreUserType.normal)
register(UserFactory, "admin", user_type=CoreUserType.admin)
register(AssetFactory)


@pytest.fixture(scope='session')
def app():
    """Create a Flask app context for tests."""
    app = create_app()
    with app.app_context():
        yield app

@pytest.fixture
def session(app, dbsession, engine):
    """Get session for current test."""
    import jb.model  # noqa: F401
    import jb.model.user  # noqa: F401
    from jb.db import Base
    Base.metadata.create_all(engine)
    return dbsession


@pytest.fixture(scope='session')
def sessionmaker(engine):
    """Get a sessionmaker that is bound to the test database engine."""
    return sqla_sessionmaker(bind=engine)


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
