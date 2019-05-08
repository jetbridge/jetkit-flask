def test_models(user, admin, asset, session):
    session.add_all((user, admin, asset))
    session.commit()
    assert user.id
    assert admin.id
    assert asset.id
