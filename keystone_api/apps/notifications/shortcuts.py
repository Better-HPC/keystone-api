"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.notifications.models import Notification
from apps.users.models import User


def send_notification(
    user: User,
    subject: str,
    plain_text: str,
    html_text: str,
    notification_type: Notification.NotificationType,
    notification_metadata: dict | None = None
) -> None:
    """Send a notification email to a specified user with both plain text and HTML content.

    Args:
        user: The user object to whom the email will be sent.
        subject: The subject line of the email.
        plain_text: The plain text version of the email content.
        html_text: The HTML version of the email content.
        notification_type: Optionally categorize the notification type.
        notification_metadata: Metadata to store alongside the notification.
    """

    send_mail(
        subject=subject,
        message=plain_text,
        from_email=settings.EMAIL_FROM_ADDRESS,
        recipient_list=[user.email],
        html_message=html_text)

    Notification.objects.create(
        user=user,
        subject=subject,
        message=plain_text,
        notification_type=notification_type,
        metadata=notification_metadata
    )


def send_notification_template(
    user: User,
    subject: str,
    template: str,
    context: dict,
    notification_type: Notification.NotificationType,
    notification_metadata: dict | None = None
) -> None:
    """Render an email template and send it to a specified user.

    Args:
        user: The user object to whom the email will be sent.
        subject: The subject line of the email.
        template: The name of the template file to render.
        context: Variable definitions used to populate the template.
        notification_type: Optionally categorize the notification type.
        notification_metadata: Metadata to store alongside the notification.

    Raises:
        UndefinedError: When template variables are not defined in the notification metadata
    """

    html_content = render_to_string(template, context, using='jinja2')
    text_content = strip_tags(html_content)

    send_notification(
        user,
        subject,
        text_content,
        html_content,
        notification_type,
        notification_metadata
    )


def send_general_notification(user: User, subject: str, message: str) -> None:
    """Send a general notification email to a specified user.

    Args:
        user: The user object to whom the email will be sent.
        subject: The subject line of the email.
        message: The message content to include.
    """

    send_notification_template(
        user=user,
        subject=subject,
        template='general.html',
        notification_type=Notification.NotificationType.general_message,
        context={'user': user, 'message': message}
    )
