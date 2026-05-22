from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        api_key = settings.RESEND_API_KEY
        from_email = settings.RESEND_FROM_EMAIL or settings.DEFAULT_FROM_EMAIL
        if not api_key:
            logger.warning("ResendEmailBackend called without RESEND_API_KEY")
            return 0

        try:
            import resend
        except ImportError:
            logger.exception("resend package missing")
            return 0

        resend.api_key = api_key
        sent = 0
        for msg in email_messages:
            for recipient in msg.to:
                try:
                    resend.Emails.send(
                        {
                            "from": from_email,
                            "to": recipient,
                            "subject": msg.subject,
                            "text": msg.body,
                            "html": msg.alternatives[0][0] if msg.alternatives else msg.body,
                        }
                    )
                    sent += 1
                except Exception:  # noqa: BLE001
                    logger.exception("Resend send failed for recipient")
                    if not self.fail_silently:
                        raise
        return sent
