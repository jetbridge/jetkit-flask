"""Mail client that doesn't actually send mail."""

from jetkit.mail.base import MailClientBase
from typing import List, Mapping
import pprint
import logging

log = logging.getLogger(__name__)


class DummyClient(MailClientBase):
    def send(
        self,
        *,
        subject: str,
        template: str,
        to: List[str],
        sender: str = None,
        variables: Mapping[str, str] = None,
        **kwargs,
    ):
        """Don't really send an email."""
        log.info(f"Pretending to send email from {sender} to {to}")
        log.info(f"  Subject: {subject}")
        log.info(f"  Template: {template}")
        log.info(f"  Variables: {pprint.pformat(variables, indent=4)}")
