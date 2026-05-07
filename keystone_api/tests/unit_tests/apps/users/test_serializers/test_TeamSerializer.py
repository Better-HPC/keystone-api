"""Unit tests for the `TeamSerializer` class."""

from django.test import TestCase

from apps.users.factories import TeamFactory
from apps.users.serializers import TeamSerializer


class ValidateMethod(TestCase):
    """Test record validation via the `validate` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.team = TeamFactory(name="Team 1")

    def test_valid_on_create_with_unique_name(self) -> None:
        """Verify a unique name passes validation on create."""

        serializer = TeamSerializer(data={"name": "Team 2"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_error_on_create_with_duplicate_name(self) -> None:
        """Verify a name that duplicates an existing slug raises a validation error."""

        serializer = TeamSerializer(data={"name": "Team 1"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_error_on_create_with_equivalent_slug(self) -> None:
        """Verify a name that slugifies identically to an existing name raises a validation error."""

        serializer = TeamSerializer(data={"name": "Team      1"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_valid_on_patch_when_name_is_unchanged(self) -> None:
        """Verify patching a team with its own existing name does not raise a validation error."""

        serializer = TeamSerializer(self.team, data={"name": "Team 1"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_on_patch_with_new_unique_name(self) -> None:
        """Verify patching a team with a new unique name passes validation."""

        serializer = TeamSerializer(self.team, data={"name": "Team 2"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_error_on_patch_with_another_teams_name(self) -> None:
        """Verify patching a team with a name already held by a different team raises a validation error."""

        TeamFactory(name="Team 2")
        serializer = TeamSerializer(self.team, data={"name": "Team 2"}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_slug_derived_from_name_on_create(self) -> None:
        """Verify the slug is generated from the name and written into validated data on create."""

        serializer = TeamSerializer(data={"name": "Team 2"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["slug"], "team-2")

    def test_slug_derived_from_name_on_patch(self) -> None:
        """Verify the slug is re-derived and written into validated data when the name changes on patch."""

        serializer = TeamSerializer(self.team, data={"name": "Alpha Squad"}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["slug"], "alpha-squad")

    def test_slug_ignored_when_name_omitted(self) -> None:
        """Verify no slug is injected into validated data when the patch omits the name field."""

        serializer = TeamSerializer(self.team, data={"description": "Updated."}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.assertNotIn("slug", serializer.validated_data)
