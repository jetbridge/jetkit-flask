"""Mail sending common functionality."""
from jetkit.mail.constant import MailerImplementation
from abc import ABC, abstractmethod
from typing import Mapping, List, TypeVar, Type, Optional, Union

MailClient = TypeVar("MailClient", bound="MailClientBase")


class MailClientBase(ABC):
    """Base mail client, allowing sending of emails via a standard interface.

    Can be used like this

    ::

        from jetkit.mail import MailerImplementation, mail_client
        mail = mail_client(impl=MailerImplementation.mailgun, from_flask=True)
        mail.send(subject="Mailgun test!", to="mischa@jetbridge.com", body="yo yo")

    If using flask, configuration is pulled from flask config object.
    """

    enabled: bool
    support_email: str
    default_sender: Optional[str]

    def __init__(self, config: Mapping[str, Union[str, int, bool]]):
        self.enabled = bool(config["EMAIL_ENABLED"])
        self.support_email = str(config["EMAIL_SUPPORT"])
        self.default_sender = str(
            config.get("EMAIL_DEFAULT_SENDER", self.support_email)
        )

    @classmethod
    def new_from_flask(cls: Type[MailClient], app=None, **kwargs) -> MailClient:
        """Create new client using flask config."""
        if not app:
            from flask import current_app

            app = current_app

        return cls(config=app.config)

    @classmethod
    def new_for_impl(
        cls, impl: MailerImplementation, from_flask: bool = True, **kwargs
    ) -> "MailClientBase":
        impl_cls: Optional[Type[MailClientBase]] = None  # FIXME: give this a type

        if impl is MailerImplementation.dummy:
            from jetkit.mail.impl.dummy import DummyClient

            impl_cls = DummyClient
        elif impl is MailerImplementation.mailgun:
            from jetkit.mail.impl.mailgun import MailgunClient

            impl_cls = MailgunClient

        if not impl_cls:
            raise NotImplementedError(f"Unimplemented mailer {impl}")

        # construct client
        if from_flask:
            return impl_cls.new_from_flask(**kwargs)
        else:
            return impl_cls(**kwargs)

    @abstractmethod
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
        """Send an email."""
        raise NotImplementedError()
