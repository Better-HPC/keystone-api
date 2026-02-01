"""Unit tests for the `Cluster` class."""

from django.test import TestCase

from apps.allocations.factories import ClusterFactory
from apps.allocations.models import Cluster
from apps.users.factories import TeamFactory


class VerifyAccessListMethod(TestCase):
    """Test the evaluation of user white/black-lists."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.cluster = ClusterFactory()
        self.team_allowed = TeamFactory()
        self.team_denied = TeamFactory()

    def test_open_mode_allows_any_team(self) -> None:
        """Verify open access mode permits all teams."""

        self.cluster.access_mode = Cluster.AccessChoices.OPEN
        self.cluster.save()

        self.assertTrue(self.cluster.verify_access_list(self.team_allowed))
        self.assertTrue(self.cluster.verify_access_list(self.team_denied))

    def test_whitelist_allows_only_listed_teams(self) -> None:
        """Verify whitelist mode restricts access to listed teams."""

        self.cluster.access_mode = Cluster.AccessChoices.WHITELIST
        self.cluster.save()
        self.cluster.access_teams.add(self.team_allowed)

        self.assertTrue(self.cluster.verify_access_list(self.team_allowed))
        self.assertFalse(self.cluster.verify_access_list(self.team_denied))

    def test_blacklist_denies_listed_teams(self) -> None:
        """Verify blacklist mode denies access to listed teams."""

        self.cluster.access_mode = Cluster.AccessChoices.BLACKLIST
        self.cluster.save()
        self.cluster.access_teams.add(self.team_denied)

        self.assertTrue(self.cluster.verify_access_list(self.team_allowed))
        self.assertFalse(self.cluster.verify_access_list(self.team_denied))
