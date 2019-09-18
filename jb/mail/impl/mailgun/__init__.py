import json

import requests
from typing import List, Mapping, Tuple
from jb.mail.base import MailClientBase

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"


class MailgunClient(MailClientBase):
    """Basic mailgun API client."""

    api_key: str
    base_url: str

    def __init__(
        self,
        enabled: bool,
        support_email: str,
        api_key: str,
        base_url: str = MAILGUN_BASE_URL,
        default_sender: str = None,
    ):
        super().__init__(
            enabled=enabled, support_email=support_email, default_sender=default_sender
        )
        self.api_key = api_key
        self.base_url = base_url

    def _auth(self) -> Tuple[str, str]:
        return "api", self.api_key

    def _send_message_url(self) -> str:
        return f"{self.base_url}/messages"

    def send(
        self,
        *,
        subject: str,
        to: List[str],
        template: str = None,
        body: str = None,
        sender: str = None,
        variables: Mapping[str, str] = None,
        **kwargs,
    ):
        variables = variables or {}

        if not self.enabled:
            return None

        if not sender:
            sender = self.default_sender

        # send message API request parameters
        params = {"from": sender, "to": to, "subject": subject}

        # template
        if template:
            params["template"] = template
            if variables and variables.keys:
                params["h:X-Mailgun-Variables"] = json.dumps(variables)
        elif not body:
            raise RuntimeError("template or body is required for sending email")
        else:
            # have body but not template
            params["text"] = body

        # do request
        res = requests.post(self._send_message_url(), auth=self._auth(), data=params)
        res.raise_for_status()
        return res.json()
