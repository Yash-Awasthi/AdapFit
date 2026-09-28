"""Plain-text mail over SMTP; logs instead of sending when no server is configured."""
import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.MAIL_FROM, to, subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_mail(to: str, subject: str, body: str) -> bool:
    """True when handed to the server. In production a missing server is an error, not a log line."""
    if not settings.SMTP_HOST:
        if settings.ENVIRONMENT.lower() == "production":
            logger.error("SMTP_HOST is not set; mail to %s not sent", to)
            return False
        logger.warning("No SMTP_HOST; mail to %s not sent:\n%s\n%s", to, subject, body)
        return True
    try:
        await asyncio.to_thread(_send, to, subject, body)
        return True
    except Exception as exc:
        logger.error("Mail to %s failed: %s", to, exc)
        return False
