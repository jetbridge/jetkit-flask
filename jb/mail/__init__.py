# use Mailgun as our default email implementation
from jb.mail.mailgun import Client as MailClient

__all__ = ("MailClient",)
