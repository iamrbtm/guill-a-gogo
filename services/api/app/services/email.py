from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config import Settings

logger = logging.getLogger("guill.email")


class EmailService:
    """Optional transactional email.

    Provider is `console` by default (logs the message) so the app works
    without any external service. Set EMAIL_PROVIDER=smtp and configure
    SMTP_* for real delivery (e.g. a self-hosted relay or Mailpit in dev).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, to: str, subject: str, body: str) -> None:
        if self.settings.email_provider == "console":
            logger.info("EMAIL (console) to=%s subject=%s\n%s", to, subject, body)
            return
        if self.settings.email_provider == "smtp":
            self._send_smtp(to, subject, body)
            return
        logger.warning("Unknown email provider %s; dropping message", self.settings.email_provider)

    def _send_smtp(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.settings.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                if self.settings.smtp_user:
                    server.starttls()
                    server.login(self.settings.smtp_user, self.settings.smtp_password or "")
                server.send_message(msg)
        except Exception as exc:  # pragma: no cover - network
            logger.error("SMTP send failed: %s", exc)
            raise


def notify_invitation(email: Optional[str], invitation_link: str, settings: Settings) -> None:
    if not email:
        return
    EmailService(settings).send(
        to=email,
        subject="You're invited to Guill-a-Gogo",
        body=(
            "You have been invited to join a private road-trip planning account.\n\n"
            f"Open this link to register your passkey: {invitation_link}\n\n"
            "This link expires in 7 days."
        ),
    )


def notify_recovery(email: str, recovery_link: str, settings: Settings) -> None:
    EmailService(settings).send(
        to=email,
        subject="Guill-a-Gogo account recovery",
        body=(
            "A recovery link was requested for your account.\n\n"
            f"If this was you, open: {recovery_link}\n\n"
            "If you did not request this, you can ignore this message."
        ),
    )
