"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import os
import re
import stat
from html import unescape

from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from jinja2 import FileSystemLoader, StrictUndefined, Template, TemplateNotFound

from apps.notifications.models import Notification
from apps.users.models import User
from plugins.email import SecureSandboxedEnvironment

__all__ = [
    'get_template',
    'format_template',
    'send_notification',
    'send_notification_template'
]


def get_template(template_name: str) -> Template:
    """Retrieve a Jinja2 email template by name.

    Attempts to return a user-defined template file from the `EMAIL_TEMPLATE_DIR` directory
    and falls back to the default application template if not found.

    Args:
        template_name: The name of the template file.

    Returns:
        A Jinja2 Template.

    Raises:
        FileNotFoundError: If the template is not found in either the custom or default location.
        PermissionError: When attempting to load a template with insecure file permissions.
    """

    loader = FileSystemLoader([settings.EMAIL_TEMPLATE_DIR, settings.EMAIL_DEFAULT_DIR])
    environment = SecureSandboxedEnvironment(undefined=StrictUndefined, autoescape=True, loader=loader)

    # Get resolved path from the loader
    try:
        source, filepath, _ = environment.loader.get_source(environment, template_name)

    except TemplateNotFound:
        raise FileNotFoundError(f"Template file not found '{template_name}'")

    # Check file permissions
    mode = os.stat(filepath).st_mode
    if mode & stat.S_IWOTH:
        raise PermissionError(f"Template file has insecure file permissions: {filepath}")

    return environment.get_template(template_name)


def format_template(template: Template, context: dict[str, any]) -> (str, str):
    """Render a Jinja2 template with context and return both HTML and plain text output.

    Args:
        template: The Jinja2 Template object to render.
        context: A dictionary of variables to inject into the template.

    Returns:
        A tuple containing the rendered HTML content and a plain text version.

    Raises:
        RuntimeError: If the rendered template is empty.
    """

    html_content = template.render(**context)

    # Replace <p> and <br> tags with line breaks
    text_content = (
        html_content.replace('<br>', '\n')
        .replace('<br/>', '\n')
        .replace('<p>', '\n\n')
        .replace('</p>', '')
    )

    text_content = strip_tags(text_content)  # Remove HTML tags
    text_content = unescape(text_content)  # Unescape special HTML characters
    text_content = re.sub(r'\n\s*\n+', '\n\n', text_content)  # Collapse excessive newlines
    text_content = re.sub(r'[ \t]+', ' ', text_content)  # Remove redundant spacing between words
    text_content = text_content.strip()  # Remove trailing whitespace

    if not (html_content and text_content):
        raise RuntimeError("Loaded template is empty.")

    return html_content, text_content


def send_notification(
    user: User,
    subject: str,
    plain_text: str,
    html_text: str,
    notification_type: Notification.NotificationType,
    notification_metadata: dict | None = None,
    save=True
) -> None:
    """Send a notification email to a specified user with both plain text and HTML content.

    Args:
        user: The user object to whom the email will be sent.
        subject: The subject line of the email.
        plain_text: The plain text version of the email content.
        html_text: The HTML version of the email content.
        notification_type: Optionally categorize the notification type.
        notification_metadata: Metadata to store alongside the notification.
        save: Whether to save the notification to the application database.
    """

    send_mail(
        subject=subject,
        message=plain_text,
        from_email=settings.EMAIL_FROM_ADDRESS,
        recipient_list=[user.email],
        html_message=html_text)

    if save:
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
    notification_metadata: dict | None = None,
    save=True
) -> None:
    """Render an email template and send it to a specified user.

    Args:
        user: The user object to whom the email will be sent.
        subject: The subject line of the email.
        template: The name of the template file to render.
        context: Variable definitions used to populate the template.
        notification_type: Optionally categorize the notification type.
        notification_metadata: Metadata to store alongside the notification.
        save: Whether to save the notification to the application database.

    Raises:
        UndefinedError: When template variables are not defined in the notification metadata
    """

    jinja_template = get_template(template)
    html_content, text_content = format_template(jinja_template, context)

    send_notification(
        user,
        subject,
        text_content,
        html_content,
        notification_type,
        notification_metadata,
        save=save
    )
