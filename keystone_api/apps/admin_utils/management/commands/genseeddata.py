"""Populate the application database with mock data.

## Arguments:

| Argument               | Description                                       |
|------------------------|---------------------------------------------------|
| --seed                 | Optional seed for the random generator.           |
| --n-staff              | Number of staff users to create.                  |
| --n-clusters           | Number of clusters to create.                     |
| --n-teams              | Number of user teams to create.                   |
| --n-team-members       | Min/max users to create per team.                 |
| --n-team-grants        | Min/max grants to create per team.                |
| --n-team-pubs          | Min/max publications to create per team.          |
| --n-team-reqs          | Min/max allocation requests to create per team.   |
| --n-req-clusters       | Min/max clusters to include per request.          |
| --n-req-jobs           | Min/max Slurm jobs to create per request.         |
| --n-req-grants         | Min/max grants to attach to each request.         |
| --n-req-pubs           | Min/max publications to attach to each request.   |
| --n-req-attachments    | Min/max file attachments to create per request.   |
| --n-req-comments       | Min/max comments to create per request.           |
| --n-req-reviewers      | Min/max staff reviewers to assign per request.    |
| --n-user-notifications | Min/max notifications to create per user.         |
"""

from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.db import transaction
from factory.random import randgen, reseed_random

from apps.allocations.factories import *
from apps.allocations.models import *
from apps.notifications.factories import NotificationFactory, PreferenceFactory
from apps.research_products.factories import *
from apps.research_products.models import *
from apps.users.factories import *
from apps.users.models import *
from . import StdOutUtils


class Command(StdOutUtils, BaseCommand):
    """Populate the database with randomized mock data."""

    help = __doc__

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Define command-line arguments.

        Args:
            parser: The parser instance to add arguments to.
        """

        range_options = dict(type=int, nargs=2, metavar=('MIN', 'MAX'), )

        parser.add_argument('--seed', type=int, help='Optional seed for the random generator.')
        parser.add_argument('--n-staff', type=int, help='Number of staff users to create.', default=100)
        parser.add_argument('--n-clusters', type=int, help='Number of clusters to create.', default=4)
        parser.add_argument('--n-teams', type=int, help='Number of user teams to create.', default=200)
        parser.add_argument('--n-team-members', **range_options, help='Min/max users to create per team.', default=[3, 5])
        parser.add_argument('--n-team-grants', **range_options, help='Min/max grants to create per team.', default=[4, 8])
        parser.add_argument('--n-team-pubs', **range_options, help='Min/max publications to create per team.', default=[4, 8])
        parser.add_argument('--n-team-reqs', **range_options, help='Min/max allocation requests to create per team.', default=[4, 8])
        parser.add_argument('--n-req-clusters', **range_options, help='Min/max clusters to include per request.', default=[0, 5])
        parser.add_argument('--n-req-jobs', **range_options, help='Min/max Slurm jobs to create per request.', default=[0, 30])
        parser.add_argument('--n-req-grants', **range_options, help='Min/max grants to attach to each request.', default=[1, 2])
        parser.add_argument('--n-req-pubs', **range_options, help='Min/max publications to attach to each request.', default=[1, 2])
        parser.add_argument('--n-req-attachments', **range_options, help='Min/max file attachments to create per request.', default=[0, 2])
        parser.add_argument('--n-req-comments', **range_options, help='Min/max comments to create per request.', default=[0, 4])
        parser.add_argument('--n-req-reviewers', **range_options, help='Min/max staff reviewers to assign per request.', default=[1, 2])
        parser.add_argument('--n-user-notifications', **range_options, help='Min/max notifications to create per user.', default=[10, 15])

    def handle(self, *args, **options) -> None:
        """Handle the command execution."""

        self._write("Generating mock data:", self.style.MIGRATE_HEADING)

        if seed := options['seed']:
            self._write(f"  Using seed: {seed}", self.style.WARNING)
            reseed_random(seed)

        self.gen_data(**options)

    @transaction.atomic
    def gen_data(
        self,
        n_staff: int,
        n_clusters: int,
        n_teams: int,
        n_team_members: tuple[int, int],
        n_team_grants: tuple[int, int],
        n_team_pubs: tuple[int, int],
        n_team_reqs: tuple[int, int],
        n_req_clusters: tuple[int, int],
        n_req_jobs: tuple[int, int],
        n_req_grants: tuple[int, int],
        n_req_pubs: tuple[int, int],
        n_req_reviewers: tuple[int, int],
        n_req_attachments: tuple[int, int],
        n_req_comments: tuple[int, int],
        n_user_notifications: tuple[int, int],
        **kwargs,
    ) -> None:
        """Populate the application database with mock data.

        Args:
            n_staff: Number of staff users to create.
            n_clusters: Number of clusters to create.
            n_teams: Number of user teams to create.
            n_team_members: Min/max users to create per team.
            n_team_grants: Min/max grants to create per team.
            n_team_pubs: Min/max publications to create per team.
            n_team_reqs: Min/max allocation requests to create per team.
            n_req_clusters: Min/max clusters to include per request.
            n_req_jobs: Min/max Slurm jobs to create per request.
            n_req_grants: Min/max grants to attach to each request.
            n_req_pubs: Min/max publications to attach to each request.
            n_req_attachments: Min/max file attachments to create per request.
            n_req_comments: Min/max comments to create per request.
            n_req_reviewers: Min/max staff reviewers to assign per request.
            n_user_notifications: Min/max notifications to create per user.
        """

        self._write("  Generating staff users...", ending=' ')
        staff = UserFactory.create_batch(n_staff, is_staff=True)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating clusters...", ending=' ')
        clusters = ClusterFactory.create_batch(n_clusters)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating teams...", ending=' ')
        teams, users = self._gen_teams(n_teams, *n_team_members)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating grants...", ending=' ')
        grants = self._gen_grants(teams, *n_team_grants)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating publications...", ending=' ')
        publications = self._gen_publications(teams, *n_team_pubs)
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating allocation requests...", ending=' ')
        self._gen_alloc_reqs(
            teams,
            staff,
            clusters,
            grants=grants,
            publications=publications,
            n_reqs=n_team_reqs,
            n_req_clusters=n_req_clusters,
            n_req_reviewers=n_req_reviewers,
            n_req_jobs=n_req_jobs,
            n_req_grants=n_req_grants,
            n_req_pubs=n_req_pubs,
            n_req_attachments=n_req_attachments,
            n_req_comments=n_req_comments,
        )
        self._write("OK", self.style.SUCCESS)

        self._write("  Generating notifications...", ending=' ')
        self._gen_notifications(users, *n_user_notifications)
        self._write("OK", self.style.SUCCESS)

    @staticmethod
    def _gen_teams(size: int, min_members: int, max_members: int) -> tuple[list[Team], list[User]]:
        """Populate the database with mock team records.

        At least one team member is guaranteed to be assigned the team owner role.

        Args:
            size: Number of teams to create.
            min_members: Minimum members to create per team.
            max_members: Maximum members to create per team.

        Returns:
            A list of the created team objects.
        """

        teams = []
        users = []
        for _ in range(size):
            team = TeamFactory()
            num_members = randgen.randint(min_members, max_members)

            # Create at least one owner member.
            owner_mem = MembershipFactory(team=team, role=Membership.Role.OWNER, user__is_staff=False)
            users.append(owner_mem.user)

            # All other members have random roles.
            for _ in range(num_members - 1):
                membership = MembershipFactory(team=team, user__is_staff=False)
                users.append(membership.user)

            teams.append(team)

        return teams, users

    @staticmethod
    def _gen_grants(teams: list[Team], n_min: int, n_max: int) -> dict[Team, list[Grant]]:
        """Populate the database with mock grant records.

        Args:
            teams: List of teams to create records for.
            n_min: Minimum records to create per team.
            n_max: Maximum records to create per team.
        """

        grants = {}
        for team in teams:
            num = randgen.randint(n_min, n_max)
            grants[team] = GrantFactory.create_batch(num, team=team)

        return grants

    @staticmethod
    def _gen_publications(teams: list[Team], n_min: int, n_max: int) -> dict[Team, list[Publication]]:
        """Populate the database with mock publication records.

        Args:
            teams: List of teams to create records for.
            n_min: Minimum records to create per team.
            n_max: Maximum records to create per team.
        """

        pubs = {}
        for team in teams:
            num = randgen.randint(n_min, n_max)
            pubs[team] = PublicationFactory.create_batch(num, team=team)

        return pubs

    @staticmethod
    def _gen_alloc_reqs(
        teams: list[Team],
        staff: list[User],
        clusters: list[Cluster],
        grants: dict[Team, list[Grant]],
        publications: dict[Team, list[Publication]],
        n_reqs: tuple[int, int],
        n_req_clusters: tuple[int, int],
        n_req_jobs: tuple[int, int],
        n_req_grants: tuple[int, int],
        n_req_pubs: tuple[int, int],
        n_req_attachments: tuple[int, int],
        n_req_comments: tuple[int, int],
        n_req_reviewers: tuple[int, int],
    ) -> None:
        """Populate the database with mock allocation request records.

        Args:
            teams: List of teams to create grants for.
            staff: List of staff users to assign as reviewers.
            clusters: List of clusters to request resources on.
            grants: Collection of mock grants generated for each team.
            publications: Collection of mock publications generated for each team.
            n_reqs: Min/max records to create per team.
            n_req_clusters: Min/max clusters to include per request.
            n_req_jobs: Min/max Slurm jobs to create per request.
            n_req_grants: Min/max grants to attach to each request.
            n_req_pubs: Min/max publications to attach to each request.
            n_req_attachments: Min/max file attachments to create per request.
            n_req_comments: Min/max comments to create per request.
            n_req_reviewers: Min/max staff reviewers to assign per request.
        """

        for team in teams:
            team_admins = list(team.get_privileged_members())
            team_members = list(team.get_all_members())
            team_grants = grants.get(team, [])
            team_publications = publications.get(team, [])

            # Create allocation requests and related records
            num_requests = randgen.randint(*n_reqs)
            for _ in range(num_requests):
                submitter = randgen.choice(team_admins)
                request = AllocationRequestFactory(team=team, submitter=submitter)

                # Assign reviewers
                if staff:
                    num_assignees = min(randgen.randint(*n_req_reviewers), len(staff))
                    request.assignees.set(randgen.sample(staff, k=num_assignees))

                # Generate reviews
                if request.status != AllocationRequest.StatusChoices.PENDING:
                    for reviewer in request.assignees.all():
                        AllocationReviewFactory(request=request, reviewer=reviewer, status=request.status)

                # Specify requested resources and simulate usage
                if clusters:
                    num_clusters = min(randgen.randint(*n_req_clusters), len(clusters))
                    for cl in randgen.sample(clusters, k=num_clusters):
                        AllocationFactory(request=request, cluster=cl)

                    num_jobs = randgen.randint(*n_req_jobs)
                    for _ in range(num_jobs):
                        JobStatsFactory(team=team, cluster=randgen.choice(clusters))

                # Attach grants
                if team_grants:
                    num_grants = min(randgen.randint(*n_req_grants), len(team_grants))
                    request.grants.set(randgen.sample(team_grants, k=num_grants))

                # Attach publications
                if team_publications:
                    num_pubs = min(randgen.randint(*n_req_pubs), len(team_publications))
                    request.publications.set(randgen.sample(team_publications, k=num_pubs))

                # Attach files
                num_attachments = randgen.randint(*n_req_attachments)
                AttachmentFactory.create_batch(num_attachments, request=request)

                # Create user/staff comments
                possible_authors = team_members + staff
                num_comments = randgen.randint(*n_req_comments)
                for _ in range(num_comments):
                    author = randgen.choice(possible_authors)
                    private = author.is_staff and randgen.choice([True, False])
                    CommentFactory(request=request, user=author, private=private)

    @staticmethod
    def _gen_notifications(users: list[User], n_min: int, n_max: int) -> None:
        """Populate the database with mock user notification records.
        
        Args:
            users: List of users to create records for.
            n_min: Minimum records to create per user.
            n_max: Maximum records to create per user.
        """

        for user in users:
            PreferenceFactory(user=user)
            NotificationFactory.create_batch(randgen.randint(n_min, n_max), user=user)
