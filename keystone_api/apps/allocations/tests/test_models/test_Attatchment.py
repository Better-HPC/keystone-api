"""Unit tests for the `Attachment` class."""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.allocations.models import AllocationRequest, Attachment
from apps.users.models import Team, User


class GetTeamMethod(TestCase):
    """Test the retrieval of an attachment's parent team via the `get_team` method.."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')
        self.allocation_request = AllocationRequest.objects.create(
            title='Test Request',
            description='A test description',
            team=self.team
        )

        self.attachment = Attachment.objects.create(
            file='dummy.file',
            name='dummy.name',
            request=self.allocation_request,
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        team = self.attachment.get_team()
        self.assertEqual(team, self.team)


class SaveMethod(TestCase):
    """Test the `save` method behavior in the `Attachment` model."""

    def setUp(self) -> None:
        """Create mock user and related records."""

        self.user = User.objects.create_user(username='pi', password='foobar123!')
        self.team = Team.objects.create(name='Test Team')
        self.allocation_request = AllocationRequest.objects.create(
            title='Test Request',
            description='A test description',
            team=self.team
        )

    def test_sets_default_name_file(self) -> None:
        """Verify the attachment name is defaults to the upload path basename."""

        path = 'directory/upload.txt'
        basename = os.path.basename(path)

        attachment = Attachment(
            request=self.allocation_request,
            file=SimpleUploadedFile(str(path), b'dummy content'),
        )

        attachment.save()
        self.assertEqual(basename, attachment.name)

    def test_custom_name_is_set(self) -> None:
        """Verify a custom name is preserved when explicitly provided."""

        path = 'directory/upload.txt'
        custom_name = 'newname.txt'

        attachment = Attachment(
            request=self.allocation_request,
            file=SimpleUploadedFile(str(path), b'dummy content'),
            name=custom_name,
        )

        attachment.save()
        self.assertEqual(custom_name, attachment.name)
