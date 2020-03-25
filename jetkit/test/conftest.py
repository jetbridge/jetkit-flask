import os
import factory
import pytest
import sqlalchemy as sa
import boto3
from unittest.mock import patch
from moto import mock_s3
from faker import Factory as FakerFactory, Faker
from flask_jwt_extended import create_access_token, create_refresh_token
from jetkit.model.user import CoreUserType
from jetkit.test.app import api_auth, api_user, create_app  # noqa: F401
from jetkit.test.model.asset import Asset
from jetkit.test.model.user import User
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
DB_CONN = os.getenv("TEST_DATABASE_URL", "postgresql:///jetkit_test")
DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()

# flask app config overrides for testing
TEST_APP_CONFIG = dict(
    SQLALCHEMY_DATABASE_URI=DB_CONN,
    AWS_S3_BUCKET_NAME="test-bucket",
    SQLALCHEMY_ECHO=bool(os.getenv("SQL_ECHO")),
    ALLOWED_AUTH_DOMAINS=["jetbridge.com"],
)


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
    app = create_app(config=TEST_APP_CONFIG)

    with app.app_context():
        yield app


@pytest.fixture(scope="session")
def _db(app):
    """Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy database connection."""
    from jetkit.test.app import db

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


@pytest.fixture
def s3_client():
    import jetkit.aws.s3

    with mock_s3():
        with patch.object(jetkit.aws.s3, "get_region") as get_region_patch:
            get_region_patch.return_value = "us-east-1"
            s3 = boto3.client("s3")
            yield s3


@pytest.fixture
def s3_bucket(app, s3_client):
    bucket_name = app.config["AWS_S3_BUCKET_NAME"]
    s3_client.create_bucket(Bucket=bucket_name)
