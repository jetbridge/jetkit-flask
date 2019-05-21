from flask_jwt_extended import create_refresh_token, get_jwt_identity
from .conftest import password as correct_password

incorrect_password = "wrong-password"


def test_login(user, client_unauthenticated, db_session, api_auth):
    db_session.add(user)
    db_session.commit()

    assert user.is_correct_password(correct_password)
    assert not user.is_correct_password(user.password)  # should fail due to comparing hash with string
    assert not user.is_correct_password(incorrect_password)

    # testing login response
    response = client_unauthenticated.post('/api/auth/login', json=dict(email=user.email, password=correct_password))
    assert response.status_code == 200
    assert response.json.get('access_token') is not None
    assert response.json.get('refresh_token') is not None
    assert response.json.get('user').get('id') is not None


def test_authentication_check_success(client, api_auth):
    response = client.get('/api/auth/check')
    # check endpoint response
    assert response.status_code == 200

    assert get_jwt_identity() is not None


def test_authentication_check_failure(client):
    # use empty auth header so request should fail as unauthorized
    response = client.get('/api/auth/check', environ_base={'HTTP_AUTHORIZATION': ''})

    # check endpoint response
    assert response.status_code == 401


def test_token_refreshing(client, user):
    response = client.get('/api/auth/refresh')  # trying to refresh with access token
    assert response.status_code == 422  # [422 UNPROCESSABLE ENTITY] because access token has different format

    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': ''})  # trying to refresh with empty header
    assert response.status_code == 401

    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': client.environ_base['REFRESH_TOKEN']})
    assert response.status_code == 200

    # try to update access token with the new refresh token for authorized user
    correct_refresh_token = create_refresh_token(identity=user)
    response = client.get('/api/auth/refresh', environ_base={'HTTP_AUTHORIZATION': f'Bearer {correct_refresh_token}'})
    assert response.status_code == 200
