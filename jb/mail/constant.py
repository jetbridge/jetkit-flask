from enum import Enum, unique


@unique
class MailerImplementation(Enum):
    dummy = "dummy"
    mailgun = "mailgun"
    ses = "ses"  # TBD
