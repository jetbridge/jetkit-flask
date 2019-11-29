"""Email clients."""

from jetkit.mail.constant import MailerImplementation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jetkit.mail.base import MailClientBase


def mail_client(
    impl: MailerImplementation, from_flask: bool = False, **kwargs
) -> "MailClientBase":
    """Get a mailer client for a given mailer implementation.

    To configure it either pass from_flask or config.
    """
    from jetkit.mail.base import MailClientBase

    return MailClientBase.new_for_impl(impl=impl, from_flask=from_flask, **kwargs)


__all__ = ["MailerImplementation"]
