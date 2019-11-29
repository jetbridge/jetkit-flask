import json

import requests
from typing import List, Mapping, Tuple
from jetkit.mail.base import MailClientBase

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"


class MailgunClient(MailClientBase):
    """Mailgun API client.

    Configuration required:

    ::

    EMAIL_DOMAIN = 'jetbridge.com'
    EMAIL_API_KEY = '12341aef13ababc-bbbba34515-a3cca4'
    """

    api_key: str
    domain: str

    def __init__(self, config):
        super().__init__(config=config)
        self.api_key = config["EMAIL_API_KEY"]
        self.domain = config["EMAIL_DOMAIN"]

    def _auth(self) -> Tuple[str, str]:
        return "api", self.api_key

    def _send_message_url(self) -> str:
        return f"{MAILGUN_BASE_URL}/{self.domain}/messages"

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
