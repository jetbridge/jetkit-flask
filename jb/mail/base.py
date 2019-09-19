"""Mail sending common functionality."""
from jb.mail.constant import MailerImplementation
from abc import ABC, abstractmethod
from typing import Mapping, List, TypeVar, Type, Optional

# config data structure in flask
# should correspond to implementation constructor args
FLASK_CONFIG_KEY = "EMAIL"

MailClient = TypeVar("MailClient", bound="MailClientBase")


class MailClientBase(ABC):
    """Base mail client, allowing sending of emails via a standard interface.


    Can be used like this

    ::

        from jb.mail import MailerImplementation, mail_client
        mail = mail_client(impl=MailerImplementation.mailgun, from_flask=True)
        mail.send(subject="Mailgun test!", to="mischa@jetbridge.com", body="yo yo")

    If using flask, configuration is pulled from the `EMAIL` config object.
    """

    enabled: bool
    support_email: str
    default_sender: Optional[str]

    def __init__(
        self, support_email: str, default_sender: str = None, enabled: bool = True
    ):
        self.enabled = enabled
        self.support_email = support_email
        self.default_sender = default_sender or support_email

    @classmethod
    def new_from_flask(cls: Type[MailClient], app=None, **kwargs) -> MailClient:
        if not app:
            from flask import current_app

            app = current_app

        conf = app.config
        if FLASK_CONFIG_KEY not in conf:
            raise Exception(f"Flask config missing {FLASK_CONFIG_KEY}")

        config_obj: Mapping[str, str] = conf.get(FLASK_CONFIG_KEY, {})
        return cls(**config_obj)

    @classmethod
    def new_for_impl(
        cls, impl: MailerImplementation, from_flask: bool = True, **kwargs
    ) -> "MailClientBase":
        impl_cls = None  # FIXME: give this a type

        if impl is MailerImplementation.dummy:
            from jb.mail.impl.dummy import DummyClient

            impl_cls = DummyClient
        elif impl is MailerImplementation.mailgun:
            from jb.mail.impl.mailgun import MailgunClient

            impl_cls = MailgunClient
        else:
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
