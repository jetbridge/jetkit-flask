import os

import factory
import pytest
import sqlalchemy as sa
from faker import Factory as FakerFactory
from faker import Faker
from flask_jwt_extended import create_access_token, create_refresh_token
from jb.model.user import CoreUserType
from jb.test.app import api_auth, api_user  # noqa: F401
from jb.test.app import create_app
from jb.test.model.asset import Asset
from jb.test.model.user import User
from pytest_factoryboy import register  # noqa: F401
from pytest_postgresql.factories import DatabaseJanitor

# for faker
LOCALE = "en_US"

db_faker: FakerFactory = FakerFactory.create()
db_faker.seed(420)  # for reproducibility

password = "super-password"


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    dob = factory.LazyAttribute(lambda x: db_faker.simple_profile()["birthdate"])
    name = factory.LazyAttribute(lambda x: db_faker.name())
    password = password


class AssetFactory(factory.Factory):
    class Meta:
        model = Asset

    s3bucket = factory.Sequence(lambda n: f"{db_faker.word()}{n}")
    s3key = factory.Sequence(lambda n: f"{db_faker.word()}{n}")
    region = "ap-southeast-1"
    mime_type = factory.Sequence(lambda n: f"{db_faker.word()}{n}")
    owner = factory.SubFactory(UserFactory)


register(UserFactory, "user", user_type=CoreUserType.normal)
register(UserFactory, "admin", user_type=CoreUserType.admin)
register(AssetFactory)

# Retrieve a database connection string from the environment
# should be a DB that doesn't exist
DB_VERSION = "10.10"
DB_CONN = os.getenv("TEST_DATABASE_URL", "postgresql:///jb_core_test")
DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()


@pytest.fixture(scope="session")
def database(request):
    """Create a Postgres database for the tests, and drop it when the tests are done."""
    host = DB_OPTS.get("host")
    port = DB_OPTS.get("port")
    user = DB_OPTS.get("username")
    db_name = DB_OPTS["database"]

    with DatabaseJanitor(user, host, port, db_name, DB_VERSION):
        yield


@pytest.fixture(scope="session")
def app(database):
    """Create a Flask app context for tests."""
    # override config for test app here
    app = create_app(dict(SQLALCHEMY_DATABASE_URI=DB_CONN))

    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def _db(app):
    """Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy database connection."""
    from jb.db import db

    # create all tables for test DB
    db.create_all()

    return db


@pytest.fixture
def client_unauthenticated(app):
    # app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def client(app, admin, user, db_session):
    # app.config['TESTING'] = True

    db_session.add(user)
    db_session.add(admin)
    db_session.commit()

    # get flask test client
    client = app.test_client()

    # create access token for the first DB user (fixture `users`)
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    # set environ http header to authenticate user
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
    client.environ_base["REFRESH_TOKEN"] = f"Bearer {refresh_token}"

    return client


@pytest.fixture
def faker():
    return Faker(LOCALE)


@pytest.fixture(autouse=True)
def session(db_session):
    """Ensure every test is inside a subtransaction giving us a clean slate each test."""
    yield db_session
