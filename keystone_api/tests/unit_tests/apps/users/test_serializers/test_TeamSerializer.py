"""Unit tests for the `TeamSerializer` class."""

from django.test import RequestFactory, TestCase

from apps.users.factories import TeamFactory, UserFactory
from apps.users.serializers import TeamSerializer


class ValidateMethod(TestCase):
    """Test record validation via the `validate` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.factory = RequestFactory()

        self.team = TeamFactory(name="Team 1")
        self.generic_user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)

    def test_valid_on_create_with_unique_name(self) -> None:
        """Verify a unique name passes validation on create."""

        serializer = TeamSerializer(data={"name": "Team 2"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_error_on_create_with_duplicate_name(self) -> None:
        """Verify a name that duplicates an existing slug raises a validation error."""

        serializer = TeamSerializer(data={"name": "Team 1"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_error_on_create_with_whitespace_variant_name(self) -> None:
        """Verify a name differing only by whitespace from an existing team raises a validation error."""

        serializer = TeamSerializer(data={"name": "Team      1"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_error_on_create_with_case_variant_name(self) -> None:
        """Verify a name differing only by letter case from an existing team raises a validation error."""

        serializer = TeamSerializer(data={"name": "team 1"})
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

    def test_error_on_create_inactive_as_non_staff(self) -> None:
        """Verify non-staff users cannot set `is_active=False` on team creation."""

        request = self.factory.post("/")
        request.user = self.generic_user

        serializer = TeamSerializer(data={"name": "New Team", "is_active": False}, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("is_active", serializer.errors)

    def test_valid_on_create_inactive_as_staff(self) -> None:
        """Verify staff users can set `is_active=False` on team creation."""

        request = self.factory.post("/")
        request.user = self.staff_user

        serializer = TeamSerializer(data={"name": "New Team", "is_active": False}, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
