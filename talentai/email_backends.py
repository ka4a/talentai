import smtplib

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.message import sanitize_address


class WhiteListSMTPBackend(EmailBackend):
    """
    SMTP Email Backend but uses whitelisting to determine if an email is to be sent
    """

    def _send(self, email_message):
        """
        A helper method that does the actual sending.
        Overridden to whitelist recipients
        """
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = []
        for addr in email_message.recipients():
            recipient = sanitize_address(addr, encoding)
            _, domain = recipient.rsplit('@', 1)
            if domain in settings.EMAIL_WHITELIST_DOMAINS:
                recipients.append(recipient)
        if not recipients:
            # treat as sent so errors aren't thrown
            return True
        message = email_message.message()
        try:
            self.connection.sendmail(
                from_email, recipients, message.as_bytes(linesep='\r\n')
            )
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True
