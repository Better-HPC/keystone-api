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

from django.core.management.base import BaseCommand
from django.db import transaction
from factory.random import randgen, reseed_random
from tqdm import tqdm

from apps.allocations.factories import AllocationFactory, AllocationRequestFactory, ClusterFactory, CommentFactory
from apps.allocations.models import AllocationRequest
from apps.notifications.factories import NotificationFactory, PreferenceFactory
from apps.research_products.factories import GrantFactory, PublicationFactory
from apps.research_products.models import Grant, Publication
from apps.users.factories import MembershipFactory, TeamFactory, UserFactory
from apps.users.models import Membership


@transaction.atomic
def gen_team(all_users):
    """Generate a team with random members."""

    team = TeamFactory()
    member_users = randgen.sample(all_users, randgen.randint(3, 4))
    for user in member_users:
        role = randgen.choice([r[0] for r in Membership.Role.choices])
        MembershipFactory(user=user, team=team, role=role)

    return team, member_users


@transaction.atomic
def gen_alloc_req_for_team(team, members, staff_users, clusters, n_requests=10):
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


@transaction.atomic
def gen_comments_for_request(request, members, staff_users, n_comments=10):
    """Generate comments for a given allocation request."""
    for _ in range(n_comments):
        possible_authors = members + staff_users
        author = randgen.choice(possible_authors)
        CommentFactory(
            request=request,
            user=author,
            private=author.is_staff and randgen.choice([True, False])
        )


class Command(BaseCommand):
    help = "Generate seed data for testing purposes."

    def add_arguments(self, parser):
        parser.add_argument('--seed', type=int, help='Optional seed for the random generator.', default=42)
        parser.add_argument('--n_users', type=int, help='Number of non-admin users to create', default=400)
        parser.add_argument('--n_staff', type=int, help='Number of admin users to create', default=100)
        parser.add_argument('--n_teams', type=int, help='Number of teams to create', default=200)
        parser.add_argument('--n_team_pubs', type=int, help='Publications per team', default=10)
        parser.add_argument('--n_team_grants', type=int, help='Grants per team', default=10)
        parser.add_argument('--n_clusters', type=int, help='Number of clusters to create', default=5)
        parser.add_argument('--n_team_reqs', type=int, help='Allocation requests per team', default=10)
        parser.add_argument('--n_reqs_comments', type=int, help='Comments per allocation request', default=10)
        parser.add_argument('--n_user_notifications', type=int, help='Notifications per user', default=15)

    def handle(self, *args, **options):
        seed = options['seed']
        n_users = options['n_users']
        n_staff = options['n_staff']
        n_teams = options['n_teams']
        n_team_pubs = options['n_team_pubs']
        n_team_grants = options['n_team_grants']
        n_clusters = options['n_clusters']
        n_team_reqs = options['n_team_reqs']
        n_reqs_comments = options['n_reqs_comments']
        n_user_notifications = options['n_user_notifications']

        if seed is not None:
            self.stdout.write(self.style.WARNING(f"Using seed: {seed}"))
            reseed_random(seed)

        self.stdout.write(self.style.SUCCESS("Seeding data..."))

        users = list(UserFactory.create_batch(n_users, is_staff=False))
        staff_users = list(UserFactory.create_batch(n_staff, is_staff=True))
        all_users = users + staff_users

        self.stdout.write(f"✓ Created {n_users} users and {n_staff} staff users")

        teams = []
        for _ in tqdm(range(n_teams), desc="Creating teams and assigning members"):
            team, member_users = gen_team(all_users)
            teams.append((team, member_users))

        self.stdout.write(f"✓ Created {n_teams} teams and assigned members")

        for team, _ in tqdm(teams, desc="Creating publications and grants"):
            with transaction.atomic():
                PublicationFactory.create_batch(n_team_pubs, team=team)
                GrantFactory.create_batch(n_team_grants, team=team)

        self.stdout.write("✓ Created publications and grants")

        clusters = ClusterFactory.create_batch(n_clusters)
        self.stdout.write(f"✓ Created {n_clusters} clusters")

        for team, members in tqdm(teams, desc="Creating allocation requests and allocations"):
            gen_alloc_req_for_team(team, members, staff_users, clusters, n_team_reqs)

        self.stdout.write("✓ Created allocation requests and allocations")

        for team, members in tqdm(teams, desc="Creating comments"):
            for request in AllocationRequest.objects.filter(team=team):
                gen_comments_for_request(request, members, staff_users, n_reqs_comments)

        self.stdout.write(f"✓ Created {n_reqs_comments} comments per allocation request")

        for user in tqdm(all_users, desc="Creating notification preferences"):
            PreferenceFactory.create(user=user)

        self.stdout.write("✓ Created notification preferences")

        for user in tqdm(all_users, desc="Creating notifications"):
            NotificationFactory.create_batch(n_user_notifications, user=user)

        self.stdout.write(self.style.SUCCESS("✓ Seeded all data successfully!"))
