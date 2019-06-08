from jb.mail import MailClient
import requests
import pytest


@pytest.fixture
def mocked_requests(mocker):
    mocker.patch.object(requests, "post", autospec=True)


def test_login(app, mocked_requests):
    mailer = MailClient()

    test_email = "test@test.com"
    mailer.send_email_to(test_email, subject="mail test client", body="automated test")
