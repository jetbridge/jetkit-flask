
correct_password = "super-password"
incorrect_password = "wrong-password"


def test_models(user, admin, client_unauthenticated, session, api_auth):
    session.add_all((user, admin))
    session.commit()

    assert user.is_correct_password(correct_password)
    assert not user.is_correct_password(user.password)  # should fail due to comparing hash with string
    assert not user.is_correct_password(incorrect_password)

    # testing login response
    response = client_unauthenticated.post('/api/auth/login', json=dict(email=user.email, password=correct_password))
    assert response.status_code == 200
    assert response.json.get('access_token') is not None
    assert response.json.get('refresh_token') is not None
    assert response.json.get('user').get('id') is not None
