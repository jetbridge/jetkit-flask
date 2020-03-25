from flask_jwt_extended import create_refresh_token, get_jwt_identity
from .conftest import password as correct_password
from jetkit.api.auth import validate_email
import pytest

incorrect_password = "wrong-password"


def test_login(user, client_unauthenticated, db_session, api_auth):
    db_session.add(user)
    db_session.commit()

    assert user.is_correct_password(correct_password)
    assert not user.is_correct_password(
        user.password
    )  # should fail due to comparing hash with string
    assert not user.is_correct_password(incorrect_password)

    # testing login response
    response = client_unauthenticated.post(
        "/api/auth/login", json=dict(email=user.email, password=correct_password)
    )
    assert response.status_code == 200
    assert response.json.get("access_token") is not None
    assert response.json.get("refresh_token") is not None
    assert response.json.get("user").get("id") is not None


def test_authentication_check_success(client, api_auth):
    response = client.get("/api/auth/check")
    # check endpoint response
    assert response.status_code == 200

    assert get_jwt_identity() is not None


def test_authentication_check_failure(client):
    # use empty auth header so request should fail as unauthorized
    response = client.get("/api/auth/check", environ_base={"HTTP_AUTHORIZATION": ""})

    # check endpoint response
    assert response.status_code == 401


def test_token_refreshing(client, user, api_auth):
    response = client.post("/api/auth/refresh")  # trying to refresh with access token
    assert response.status_code == 422

    response = client.post(
        "/api/auth/refresh", environ_base={"HTTP_AUTHORIZATION": ""}
    )  # trying to refresh with empty header
    assert response.status_code == 401

    response = client.post(
        "/api/auth/refresh",
        environ_base={"HTTP_AUTHORIZATION": client.environ_base["REFRESH_TOKEN"]},
    )
    assert response.status_code == 200

    # try to update access token with the new refresh token for authorized user
    correct_refresh_token = create_refresh_token(identity=user)
    response = client.post(
        "/api/auth/refresh",
        environ_base={"HTTP_AUTHORIZATION": f"Bearer {correct_refresh_token}"},
    )
    assert response.status_code == 200


def test_sign_up(client_unauthenticated, app, api_auth, client):
    test_email = "testsignup@jetbridge.com"
    test_password = "testo"
    sign_up_response = client_unauthenticated.post(
        "/api/auth/sign-up", json=dict(email=test_email, password=test_password)
    )
    assert sign_up_response.status_code == 200
    assert sign_up_response.json["email"] == test_email

    log_in_response = client_unauthenticated.post(
        "/api/auth/login", json=dict(email=test_email, password=test_password)
    )

    assert log_in_response.status_code == 200
    assert log_in_response.json["access_token"] is not None
    assert log_in_response.json["refresh_token"] is not None
    assert log_in_response.json["user"].get("id") is not None

    sign_up_response = client_unauthenticated.post(
        "/api/auth/sign-up", json=dict(email=test_email, password=test_password)
    )

    assert not sign_up_response == 200


@pytest.mark.parametrize(
    "test_email,allowed_domains,allowed_emails,expected",
    [
        ("me@mail.com", ["jetbridge.com"], None, False),
        ("me@mail.com", ["mail.com"], None, True),
        ("me@mail.com", None, ["me@mail.com"], True),
        ("me@mail.com", ["mail.com"], ["me@mail.com"], True),
        ("me@mail.com", ["jetbridge.com"], ["me@mail.com"], True),
        ("me@mail.com", ["mail.com", "another.com"], ["other@other.com"], True),
        ("me@mail.com", None, ["someothermail@gmail.com", "me@mail.com"], True),
        ("me@mail.com", None, None, False),
        ("me@mail.com", ["me@otherdomain.com"], None, False),
        ("me@mail.com", ["me@otherdomain.com", "another@dom.ain"], None, False),
        ("me@mail.com", ["me@otherdomain.com"], ["other@email.com"], False),
        ("me@mail.com", [], [], False),
        ("me@mail.com", [], ["another@email.com"], False),
        ("me@mail.com", ["other.com"], [], False),
    ],
)
def test_validate_email(test_email, allowed_domains, allowed_emails, expected):
    assert validate_email(test_email, allowed_domains, allowed_emails) == expected
