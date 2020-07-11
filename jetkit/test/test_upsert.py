from jetkit.test.app import db
from jetkit.db.upsert import Upsertable, OnConflictBehavior


class UserWithEmail(db.Model, Upsertable):
    email = db.Column(db.Text(), unique=True)
    counter = db.Column(db.Integer())


def test_upsert_on_conflict_do_something_or_nothing(session):
    email = "mischa@jetbridge.com"
    u1 = UserWithEmail.upsert_row(
        UserWithEmail, index_elements=["email"], values=dict(email=email, counter=1)
    )

    assert u1.counter == 1

    # on conflict do update
    UserWithEmail.upsert_row(
        UserWithEmail, index_elements=["email"], values=dict(email=email, counter=2)
    )
    assert u1.counter == 2

    # on conflict do nothing
    UserWithEmail.upsert_row(
        UserWithEmail,
        index_elements=["email"],
        values=dict(email=email, counter=3),
        on_conflict=OnConflictBehavior.ON_CONFLICT_DO_NOTHING,
    )
    assert u1.counter == 2
