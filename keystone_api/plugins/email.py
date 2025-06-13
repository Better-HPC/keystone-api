from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.text import slugify


class EmlFileBasedEmailBackend(BaseEmailBackend):

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)

        self._output_dir = getattr(settings, 'EMAIL_FILE_PATH')
        if self._output_dir is None:
            raise ImproperlyConfigured('EMAIL_FILE_PATH must be set to use EmlFileBasedEmailBackend.')

        if not self._output_dir.exists():
            raise RuntimeError(f'Directory does not exist: {self._output_dir}')

    def _generate_file_path(self, message) -> Path:

        # Generate a file name from the message subject
        filename = slugify(message.subject)
        return self._output_dir / f"{filename}.eml"

    def write_message(self, message) -> None:
        """Write an email message to disk.

        Args:
            message: The message to write.
        """

        filename = self._generate_file_path(message)
        with open(filename, 'a') as out_file:
            out_file.write(message.message().as_string())

    def send_messages(self, email_messages) -> None:
        """Send a list of email messages.

        Args:
            email_messages: The messages to send.
        """

        for message in email_messages:
            self.write_message(message)
