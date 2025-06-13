import os

from django.core.mail.backends.filebased import EmailBackend
from django.utils.text import slugify


class EmlFileBasedEmailBackend(EmailBackend):

    def __get_filename(self, message):

        # Generate a file name from the message subject
        filename = slugify(message.subject)
        full_path = os.path.join(self.file_path, f"{filename}.eml")

        # Avoid overwriting existing files by appending a numeric suffix if necessary
        counter = 1
        while os.path.exists(full_path):
            full_path = os.path.join(self.file_path, f"{filename}-{counter}.eml")
            counter += 1

        return full_path

    def write_message(self, message):

        filename = self.__get_filename(message)
        with open(filename, 'a') as out_file:
            out_file.write(message.message().as_string())

    def send_messages(self, email_messages):
        for message in email_messages:
            self.write_message(message)
