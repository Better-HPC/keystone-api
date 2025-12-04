"""Unit tests for the `Attachment` class."""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.allocations.factories import AllocationRequestFactory, AttachmentFactory
from apps.allocations.models import Attachment
from apps.users.factories import TeamFactory, UserFactory


class GetTeamMethod(TestCase):
    """Test the retrieval of an attachment's parent team via the `get_team` method."""

    def setUp(self) -> None:
        """Create mock user records"""

        self.team = TeamFactory()
        self.allocation_request = AllocationRequestFactory(team=self.team)

        # Create an attachment linked to a request submitted by `self.team`
        self.attachment = AttachmentFactory(
            request=self.allocation_request,
        )

    def test_get_team(self) -> None:
        """Verify the `get_team` method returns the correct `Team` instance."""

        self.assertEqual(self.team, self.attachment.get_team())


class SaveMethod(TestCase):
    """Test the `save` method behavior in the `Attachment` model."""

    def setUp(self) -> None:
        """Create mock user and related records."""

        self.user = UserFactory()
        self.team = TeamFactory()
        self.allocation_request = AllocationRequestFactory(team=self.team)

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
