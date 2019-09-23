"""Email clients."""

from jb.mail.constant import MailerImplementation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jb.mail.base import MailClientBase


def mail_client(
    impl: MailerImplementation, from_flask: bool = False
) -> "MailClientBase":
    from jb.mail.base import MailClientBase

    return MailClientBase.new_for_impl(impl=impl, from_flask=from_flask)


__all__ = ["MailerImplementation"]
