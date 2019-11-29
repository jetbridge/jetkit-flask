from jetkit.mail.base import MailClientBase
from jetkit.mail.constant import MailerImplementation
import requests
import pytest
from unittest.mock import patch


@pytest.fixture
def dummy_client():
    yield MailClientBase.new_for_impl(
        impl=MailerImplementation.dummy,
        from_flask=False,
        config=dict(EMAIL_ENABLED=True, EMAIL_SUPPORT="test@test.com"),
    )


@pytest.fixture
def mailgun_client_flask():
    yield MailClientBase.new_for_impl(
        impl=MailerImplementation.mailgun, from_flask=True
    )


@pytest.fixture
def mailgun_client_config():
    yield MailClientBase.new_for_impl(
        impl=MailerImplementation.mailgun, config={"EMAIL_ENABLED": False}
    )


@pytest.fixture
def mocked_requests(mocker):
    mocker.patch.object(requests, "post", autospec=True)


def test_login(app, mocked_requests, mailgun_client_flask, mailgun_client_config):
    test_email = "test@test.com"
    mailgun_client_flask.send(
        to=[test_email], subject="mail test client", body="automated test"
    )
    mailgun_client_config.send(
        to=[test_email], subject="mail test client", body="automated test"
    )


def test_dummy_mailer(dummy_client):
    with patch.object(dummy_client, "send") as send_patch:
        dummy_client.send()
        send_patch.assert_called_once()
