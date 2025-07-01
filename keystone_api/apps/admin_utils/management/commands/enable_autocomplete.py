"""A Django management command that enables Bash autocompletion for the keystone-api command."""

import shutil
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Enable autocompletion for the keystone-api command-line tool."""

    help = __doc__

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        try:
            self._handle()

        except KeyboardInterrupt:
            print()  # Move bash prompt to a new line
            exit(1)

    def _handle(self) -> None:
        """Execute the application logic."""

        # Find the user's shell config files
        if not (profile_paths := self.get_profile_paths()):
            self.stderr.write('No .bash_profile or .bashrc file found.')
            exit(1)

        if not self.prompt_for_confirmation(profile_paths):
            return

        # Copy the completion script into the user's home directory
        completion_script_src = Path(__file__).parent.resolve() / 'keystone_autocomplete'
        completion_script_dest = Path.home() / '.keystone_autocomplete'
        shutil.copyfile(completion_script_src, completion_script_dest)

        # Source the completion file in the user's shell configuration
        for path in profile_paths:
            with path.open(mode='a') as file:
                file.write('\nsource ~/.keystone_autocomplete\n')

    @staticmethod
    def prompt_for_confirmation(profile_paths: list[Path]) -> bool:
        """Prompt the user to confirm command execution.

        Returns:
            A boolean indicating whether the user confirmed execution.
        """

        path_names = ' and '.join(path.name for path in profile_paths)
        print(
            'This command will make the following changes:\n'
            '  - A file `.keystone_autocomplete` will be added to your home directory\n'
            f'  - A line of setup code will be added to your {path_names} file\n'
        )

        while True:
            answer = input('Do you want to continue? [y/N]: ').lower()
            if answer == 'y':
                return True

            elif answer in ('n', ''):
                return False

            print('Unrecognized input.')

    @staticmethod
    def get_profile_paths() -> list[Path]:
        """Search the user's home directory for shell configuration files.

        Returns:
            A list of shell configuration files found in the user's home directory.
        """

        bashrc_path = Path.home() / '.bashrc'
        zshrc_path = Path.home() / '.zshrc'
        paths = [bashrc_path, zshrc_path]
        return [p for p in paths if p.exists()]
