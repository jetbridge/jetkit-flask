def test_models(user, admin, asset):
    assert user.id
    assert admin.id
    assert asset.id
