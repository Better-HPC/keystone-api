"""Extends the `django` package with custom email backends.

Email backends define how Django delivers email. This plugin provides
backends for writing custom email messages a `.eml` files in a configured
directory, rather than sending them via external service like SMTP.
"""

from datetime import datetime
from pathlib import Path
from types import BuiltinFunctionType, BuiltinMethodType

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.text import slugify
from jinja2.sandbox import SandboxedEnvironment

__all__ = ['EmlFileEmailBackend', 'SecureSandboxedEnvironment']


class EmlFileEmailBackend(BaseEmailBackend):
    """A Django email backend that writes email messages to .eml files on disk.

    This backend writes each outgoing email message to a file in the directory
    specified by the `EMAIL_FILE_PATH` setting. Output filenames are derived
    from the message subject. If the subject is empty or slugifies to an empty
    string, the current timestamp is used instead. Duplicate file names are
    overwritten.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the backend and validate relevant application settings."""

        super().__init__(*args, **kwargs)

        self._output_dir = getattr(settings, 'EMAIL_FILE_PATH')
        if self._output_dir is None:
            raise ImproperlyConfigured('EMAIL_FILE_PATH must be set to use EmlFileBasedEmailBackend.')

        if not self._output_dir.exists():
            raise RuntimeError(f'Directory does not exist: {self._output_dir}')

    def generate_file_path(self, message: EmailMessage) -> Path:
        """Generate the destination file path for the given email message.

        Args:
            message: The email message instance.

        Returns:
            Path: The full path to an output .eml file.
        """

        # Generate a file name from the message subject
        subject = getattr(message, 'subject', '')
        filename = slugify(subject)

        # If there is no subject, default to  the datetime
        if not filename.strip('-'):
            filename = str(datetime.now().timestamp())

        return self._output_dir / f"{filename}.eml"

    def write_message(self, message: EmailMessage) -> None:
        """Write an email message to disk.

        Args:
            message: The message to write.
        """

        filename = self.generate_file_path(message)
        with open(filename, 'w') as out_file:
            out_file.write(message.message().as_string())

    def send_messages(self, email_messages: list[EmailMessage]) -> None:
        """Send a list of email messages.

        Args:
            email_messages: The messages to send.
        """

        for message in email_messages:
            self.write_message(message)


class SecureSandboxedEnvironment(SandboxedEnvironment):
    """A security hardened Jinja2 environment that blocks access to insecure Django functionality."""

    _forbidden_attrs = {'objects', 'password', 'history'}
    _allowed_constructors = {str, int, float, bool, list, tuple, dict, set, frozenset}

    def is_safe_attribute(self, obj: object, attr: str, value: any) -> bool:
        """Block access to private and forbidden attributes."""

        # Block private methods and explicitly forbidden names
        if attr.startswith('_') or attr in self._forbidden_attrs:
            return False

        return super().is_safe_attribute(obj, attr, value)

    def is_safe_callable(self, obj: callable) -> bool:
        """Block all callables unless it's a constructor/method from a primitive type."""

        is_builtin_constructor = obj in self._allowed_constructors
        is_builtin_method = isinstance(obj, (BuiltinFunctionType, BuiltinMethodType))
        return is_builtin_constructor or is_builtin_method
