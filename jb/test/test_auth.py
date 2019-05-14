from flask_jwt_extended import get_raw_jwt, decode_token, create_refresh_token, get_jwt_identity

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


def test_authentication_check_success(user, client, client_unauthenticated, session, api_auth):
    session.add(user)
    session.commit()

    response = client.get('/api/auth/check')
    # check endpoint response
    assert response.status_code == 422

    access_token = client_unauthenticated.post('/api/auth/login', json=dict(email=user.email, password=correct_password)).json.get('access_token')
    response = client.get('/api/auth/check', environ_base={'HTTP_AUTHORIZATION': f'Bearer {access_token}'})
    assert response.status_code == 200

    assert get_jwt_identity() is not None


def test_authentication_check_failure(client):
    # use empty auth header so request should fail as unauthorized
    response = client.get('/api/auth/check', environ_base={'HTTP_AUTHORIZATION': ''})

    # check endpoint response
    assert response.status_code == 401


def test_token_refreshing(user, client, session, api_auth, client_unauthenticated):
    session.add(user)
    session.commit()
    tokens = client_unauthenticated.post('/api/auth/login', json=dict(email=user.email, password=correct_password))

    print(tokens)
    response = client.get('/api/auth/refresh')  # trying to refresh with access token
    assert response.status_code == 422  # [422 UNPROCESSABLE ENTITY] because access token has different format

    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': ''})  # trying to refresh with empty header
    assert response.status_code == 401

    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': f'Bearer {tokens.json.get("refresh_token")}'})
    assert response.status_code == 200

    # try to update access token with the new refresh token for authorized user
    correct_refresh_token = create_refresh_token(identity=user.id)
    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': f'Bearer {correct_refresh_token}'})
    assert response.status_code == 200
