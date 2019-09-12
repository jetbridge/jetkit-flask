import json

import requests
from typing import Dict, Tuple, Optional
from flask import current_app

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"


class BaseClient:
    def __init__(
        self,
        enabled: bool,
        support_email: str,
        api_key: str,
        base_url: str = MAILGUN_BASE_URL,
        default_sender: str = None,
    ):
        self.enabled = enabled
        self.support_email = support_email
        self.api_key = api_key
        self.base_url = base_url
        self.default_sender = default_sender or support_email

    def _auth(self) -> Tuple[str, str]:
        return "api", self.api_key

    def _send_message_url(self) -> str:
        return f"{self.base_url}/messages"

    def send_email_to(
        self,
        email: str,
        *,
        subject: str,
        body: str = None,
        sender: str = None,
        template: str = None,
        variables: Dict[str, str] = None,
    ) -> Optional[Dict]:
        variables = variables or {}

        if not self.enabled:
            return None

        if not sender:
            sender = self.default_sender

        # send message API request parameters
        params = {"from": sender, "to": email, "subject": subject}

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


class Client(BaseClient):
    """Mailgun client that looks up configuration in current Flask app."""

    def __init__(self):
        super().__init__(
            enabled=current_app.config["EMAIL_SENDING_ENABLED"],
            support_email=current_app.config["SUPPORT_EMAIL"],
            api_key=current_app.config["MAILGUN_API_KEY"],
            base_url=current_app.config.get("MAILGUN_BASE_URL"),
            default_sender=current_app.config.get("MAILGUN_DEFAULT_SENDER"),
        )
