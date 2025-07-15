"""Populate the application database with mock data.

## Arguments:

| Argument               | Description                                       |
|------------------------|---------------------------------------------------|
| --seed                 | Optional seed for the random generator.           |
| --n_users              | Number of non-admin users.                        |
| --n_staff              | Number of admin users.                            |
| --n_teams              | Number of teams.                                  |
| --n_team_pubs          | Number of publications per team.                  |
| --n_team_grants        | Number of grants per team.                        |
| --n_clusters           | Number of clusters.                               |
| --n_team_reqs          | Number of allocation requests per team.           |
| --n_reqs_comments      | Number of comments per allocation request.        |
| --n_user_notifications | Number of notifications per user.                 |
"""

from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.db import transaction
from factory.random import randgen, reseed_random

from apps.allocations.factories import *
from apps.allocations.models import AllocationRequest
from apps.notifications.factories import *
from apps.research_products.factories import *
from apps.research_products.models import Grant, Publication
from apps.users.factories import *
from apps.users.models import Membership
from . import StdOutUtils


class Command(StdOutUtils, BaseCommand):
    """Populate the database with randomized mock data."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The parser instance to add arguments to.
        """

        parser.add_argument('--seed', type=int, help='Optional seed for the random generator.')
        parser.add_argument('--n_users', type=int, help='Number of non-admin users to create', default=400)
        parser.add_argument('--n_staff', type=int, help='Number of admin users to create', default=100)
        parser.add_argument('--n_teams', type=int, help='Number of teams to create', default=200)
        parser.add_argument('--n_team_pubs', type=int, help='Publications per team', default=10)
        parser.add_argument('--n_team_grants', type=int, help='Grants per team', default=10)
        parser.add_argument('--n_clusters', type=int, help='Number of clusters to create', default=5)
        parser.add_argument('--n_team_reqs', type=int, help='Allocation requests per team', default=10)
        parser.add_argument('--n_reqs_comments', type=int, help='Comments per allocation request', default=10)
        parser.add_argument('--n_user_notifications', type=int, help='Notifications per user', default=15)

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        self._write("Generating mock data:", self.style.MIGRATE_HEADING)

        if seed := options['seed']:
            self._write(f"  Using seed: {seed}", self.style.WARNING)
            reseed_random(seed)

        self.gen_data(
            n_users=options['n_users'],
            n_staff=options['n_staff'],
            n_teams=options['n_teams'],
            n_team_pubs=options['n_team_pubs'],
            n_team_grants=options['n_team_grants'],
            n_clusters=options['n_clusters'],
            n_team_reqs=options['n_team_reqs'],
            n_reqs_comments=options['n_reqs_comments'],
            n_user_notifications=options['n_user_notifications'],
        )

    @transaction.atomic
    def gen_data(self, n_clusters, n_reqs_comments, n_staff, n_team_grants, n_team_pubs, n_team_reqs, n_teams, n_user_notifications, n_users):

        self._write("  Generating user accounts...", ending=' ')
        users = list(UserFactory.create_batch(n_users, is_staff=False))
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating staff accounts... ", ending=' ')
        staff_users = list(UserFactory.create_batch(n_staff, is_staff=True))
        self._write("OK", self.style.SUCCESS)

        teams = []
        all_users = users + staff_users

        self._write("  Generating teams...", ending=' ')
        for _ in range(n_teams):
            team, member_users = self._gen_team(all_users)
            teams.append((team, member_users))

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating publications...", ending=' ')
        for team, _ in teams:
            PublicationFactory.create_batch(n_team_pubs, team=team)

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating grants...", ending=' ')
        for team, _ in teams:
            GrantFactory.create_batch(n_team_grants, team=team)

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating clusters...", ending=' ')
        clusters = ClusterFactory.create_batch(n_clusters)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating allocation requests...", ending=' ')
        for team, members in teams:
            self._gen_alloc_req_for_team(team, members, staff_users, clusters, n_team_reqs)

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating comments...", ending=' ')
        for team, members in teams:
            for request in AllocationRequest.objects.filter(team=team):
                self._gen_comments_for_request(request, members, staff_users, n_reqs_comments)

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating notification preferences...", ending=' ')
        for user in all_users:
            PreferenceFactory.create(user=user)

        self._write("OK", self.style.SUCCESS)
        self._write("  Generating notifications...", ending=' ')
        for user in all_users:
            NotificationFactory.create_batch(n_user_notifications, user=user)

        self._write("OK", self.style.SUCCESS)

    @staticmethod
    def _gen_team(all_users):
        """Generate a team with random members."""

        team = TeamFactory()
        members = randgen.sample(all_users, randgen.randint(3, 4))
        for user in members:
            role = randgen.choice([r[0] for r in Membership.Role.choices])
            MembershipFactory(user=user, team=team, role=role)

        return team, members

    @staticmethod
    def _gen_alloc_req_for_team(team, members, staff_users, clusters, n_requests=10):
        """Generate allocation requests for a team with random members and staff users."""

        team_grants = list(Grant.objects.filter(team=team))
        team_publications = list(Publication.objects.filter(team=team))
        for _ in range(n_requests):
            submitter = randgen.choice(members)
            request = AllocationRequestFactory(team=team, submitter=submitter)

            assignees = randgen.sample(staff_users,
                k=randgen.randint(1, min(2, len(staff_users))))
            request.assignees.set(assignees)

            if team_publications:
                pubs = randgen.sample(team_publications,
                    k=randgen.randint(1, min(2, len(team_publications))))
                request.publications.set(pubs)

            if team_grants:
                grants = randgen.sample(team_grants,
                    k=randgen.randint(1, min(2, len(team_grants))))
                request.grants.set(grants)

            for _ in range(randgen.randint(3, 4)):
                AllocationFactory(request=request, cluster=randgen.choice(clusters))

    @staticmethod
    def _gen_comments_for_request(request, members, staff_users, n_comments=10):
        """Generate comments for a given allocation request."""

        for _ in range(n_comments):
            possible_authors = members + staff_users
            author = randgen.choice(possible_authors)
            CommentFactory(
                request=request,
                user=author,
                private=author.is_staff and randgen.choice([True, False])
            )
