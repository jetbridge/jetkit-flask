from jetkit.test.model.user import User


def test_can_get_by_extid(user, session):
    session.add(user)
    session.commit()
    assert user.extid
    assert User.get_by_extid(user.extid) is user
