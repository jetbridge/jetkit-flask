def test_models(user, admin, asset, db_session):
    db_session.add_all((user, admin, asset))
    db_session.commit()
    assert user.id
    assert admin.id
    assert asset.id
