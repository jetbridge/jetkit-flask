"""Create fake models for tests and seeding dev DB."""
import factory
from faker import Factory as FakerFactory
from jb.db import Session
from jb.test.model.asset import Asset
from jb.test.model.user import User
from pytest_factoryboy import register
from werkzeug.security import generate_password_hash
from yaspin import yaspin

faker: FakerFactory = FakerFactory.create()
faker.seed(420)  # for reproducibility
session = Session()


def seed_db():
    with yaspin(text="Seeding database...", color="yellow") as spinner:
        for i in range(1, 2):
            session.add(Asset.create())
            session.add(UserFactory.create())
    session.commit()
    print("Database seeded.")
    spinner.ok("✅ ")


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    dob = factory.LazyAttribute(lambda x: faker.simple_profile()['birthdate'])
    name = factory.LazyAttribute(lambda x: faker.name())
    _password = factory.LazyAttribute(lambda x: generate_password_hash('super-password'))


@register
class AssetFactory(factory.Factory):
    class Meta:
        model = Asset

    s3bucket = factory.Sequence(lambda n: f'{faker.word()}{n}')
    s3key = factory.Sequence(lambda n: f'{faker.word()}{n}')
    mime_type = factory.Sequence(lambda n: f'{faker.word()}{n}')
    owner = factory.SubFactory(UserFactory)
