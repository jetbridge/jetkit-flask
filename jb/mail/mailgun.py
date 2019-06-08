import json

import requests
from typing import Dict, Tuple, Optional
from flask import current_app

MAILGUN_BASE_URL = "https://api.mailgun.net/v3"


class Client:
    def __init__(self):
        self.base_url = current_app.config.get("MAILGUN_BASE_URL", MAILGUN_BASE_URL)
        self.enabled = current_app.config["EMAIL_SENDING_ENABLED"]
        self.support_email = current_app.config["SUPPORT_EMAIL"]
        self.api_key = current_app.config["MAILGUN_API_KEY"]
        self.default_sender = current_app.config.get(
            "MAILGUN_DEFAULT_SENDER", self.support_email
        )

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
        variables: Dict[str, str] = {},
    ) -> Optional[Dict]:
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
