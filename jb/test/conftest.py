import os

import sqlalchemy as sa

import pytest
from faker import Faker
from jb.db.fixture import AssetFactory, UserFactory
from jb.model.user import CoreUserType
from jb.test.app import create_app
from pytest_factoryboy import register
from pytest_postgresql.factories import (drop_postgresql_database, init_postgresql_database)
from jb.test.app import api_auth  # noqa: F401

# for faker
LOCALE = "en_US"

register(UserFactory, "user", user_type=CoreUserType.normal)
register(UserFactory, "admin", user_type=CoreUserType.admin)
register(AssetFactory)

# Retrieve a database connection string from the environment
# should be a DB that doesn't exist
DB_CONN = os.getenv('TEST_DATABASE_URL', 'postgresql:///jb_core_test')
DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()


@pytest.fixture(scope='session')
def database(request):
    """Create a Postgres database for the tests, and drop it when the tests are done."""
    pg_host = DB_OPTS.get("host")
    pg_port = DB_OPTS.get("port")
    pg_user = DB_OPTS.get("username")
    pg_db = DB_OPTS["database"]

    db = init_postgresql_database(pg_user, pg_host, pg_port, pg_db)

    yield db

    @request.addfinalizer
    def drop_database():
        drop_postgresql_database(pg_user, pg_host, pg_port, pg_db, 9.6)


@pytest.fixture(scope='session')
def app(database):
    """Create a Flask app context for tests."""
    # override config for test app here
    app = create_app(dict(SQLALCHEMY_DATABASE_URI=DB_CONN, ))

    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def _db(app):
    """Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy database connection."""
    from jb.db import db

    # create all tables for test DB
    db.create_all()

    return db


@pytest.fixture
def session(_db):
    yield _db.session


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
