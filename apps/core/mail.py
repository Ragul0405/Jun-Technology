"""
Outgoing mail.

Settings come from the dashboard (`EmailSettings`) when the super admin has
enabled them; otherwise the project falls back to the DJANGO_EMAIL_*
environment variables so a server can be configured without the dashboard.
"""

import logging

from django.conf import settings as django_settings
from django.core.mail import EmailMessage, get_connection
from django.utils import timezone

from .models import EmailSettings

logger = logging.getLogger(__name__)


def build_connection(config=None):
    """An SMTP connection from the dashboard settings, or the env fallback."""
    config = config or EmailSettings.load()
    if not config.is_configured:
        return get_connection(fail_silently=False)
    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=config.host,
        port=config.port,
        username=config.username or None,
        password=config.password or None,
        use_tls=config.use_tls,
        use_ssl=config.use_ssl,
        timeout=config.timeout or 20,
        fail_silently=False,
    )


def sender_address(config=None):
    config = config or EmailSettings.load()
    return config.from_email or django_settings.DEFAULT_FROM_EMAIL


def recipient_address(config=None):
    """Where enquiries go — the dashboard value wins over the env variable."""
    config = config or EmailSettings.load()
    return config.notify_email or getattr(
        django_settings, "CONTACT_NOTIFY_EMAIL", ""
    )


def build_subject(prefix, subject):
    """Join prefix and subject with exactly one space.

    Form fields strip surrounding whitespace, so the prefix can never be
    relied on to carry its own trailing space.
    """
    prefix = (prefix or "").strip()
    return f"{prefix} {subject}".strip() if prefix else subject


def send_enquiry_notification(message):
    """Email a contact-form submission. Never raises — the visitor comes first."""
    config = EmailSettings.load()
    recipient = recipient_address(config)
    if not recipient:
        return False

    body = (
        f"New enquiry from the website.\n\n"
        f"Name:    {message.name}\n"
        f"Email:   {message.email}\n"
        f"Phone:   {message.phone or '—'}\n"
        f"Subject: {message.subject}\n"
        f"Sent:    {timezone.localtime(message.created_at):%d %B %Y, %H:%M}\n\n"
        f"{message.message}\n"
    )

    email = EmailMessage(
        subject=build_subject(config.subject_prefix, message.subject),
        body=body,
        from_email=sender_address(config),
        to=[recipient],
        reply_to=[message.email] if config.reply_to_sender else None,
        connection=build_connection(config),
    )
    try:
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Could not email enquiry #%s", message.pk)
        return False


def send_test_email(recipient):
    """Used by the dashboard's “Send test email” button. Returns (ok, error)."""
    config = EmailSettings.load()
    try:
        EmailMessage(
            subject="Test email from your website",
            body=(
                "This is a test from the Jun Technology dashboard.\n\n"
                "If you are reading this, your mail settings are working and "
                "contact-form enquiries will reach this inbox.\n"
            ),
            from_email=sender_address(config),
            to=[recipient],
            connection=build_connection(config),
        ).send(fail_silently=False)
        error = ""
        ok = True
    except Exception as exc:  # surfaced to the admin, not the visitor
        ok = False
        error = f"{type(exc).__name__}: {exc}"
        logger.warning("Test email failed: %s", error)

    EmailSettings.objects.filter(pk=1).update(
        last_test_at=timezone.now(), last_test_ok=ok, last_test_error=error[:2000]
    )
    return ok, error
