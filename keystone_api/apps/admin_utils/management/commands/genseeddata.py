""" Command to generate seed data for testing purposes.
This command creates a large set of users, teams, publications, grants, allocation requests,
allocations, comments, notifications, and user preferences.

It uses the `factory_boy` library to generate realistic data and the `Faker` library
to create fake data for various fields. The command can be run with an optional seed
to ensure reproducibility of the generated data.

# Arguments:
| Argument    | Description                                                           |
|-------------|-----------------------------------------------------------------------|
| --seed      | Optional seed for random number generators to ensure reproducibility. |

# Usage:
```bash
python manage.py genseeddata --seed 12345
```

"""

import factory
from django.db import transaction
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apps.users.models import User, Team, Membership
from apps.users.factories import UserFactory, TeamFactory, MembershipFactory
from apps.allocations.models import AllocationRequest, Comment
from apps.allocations.factories import (
    ClusterFactory,
    AllocationRequestFactory,
    AllocationFactory,
    CommentFactory,
)
from apps.research_products.models import Grant, Publication
from apps.research_products.factories import GrantFactory, PublicationFactory
from apps.notifications.models import Notification, Preference
from apps.notifications.factories import NotificationFactory, PreferenceFactory
from apps.factories.providers import global_provider

@transaction.atomic
def gen_team(all_users):
    """Generate a team with random members."""
    team = TeamFactory()
    member_users = global_provider.random.sample(all_users, global_provider.random.randint(3, 4))
    for user in member_users:
        role = global_provider.random.choice([r[0] for r in Membership.Role.choices])
        MembershipFactory(user=user, team=team, role=role)
    return team, member_users

@transaction.atomic
def gen_alloc_req_for_team(team, members, staff_users, clusters, n_requests=10):
    """Generate allocation requests for a team with random members and staff users."""
    team_grants = list(Grant.objects.filter(team=team))
    team_publications = list(Publication.objects.filter(team=team))
    for _ in range(n_requests):
        submitter = global_provider.random.choice(members)
        request = AllocationRequestFactory(team=team, submitter=submitter)

        assignees = global_provider.random.sample(staff_users,
                                                  k=global_provider.random.randint(1, min(2, len(staff_users))))
        request.assignees.set(assignees)

        if team_publications:
            pubs = global_provider.random.sample(team_publications,
                                                 k=global_provider.random.randint(1, min(2, len(team_publications))))
            request.publications.set(pubs)

        if team_grants:
            grants = global_provider.random.sample(team_grants,
                                                   k=global_provider.random.randint(1, min(2, len(team_grants))))
            request.grants.set(grants)

        for _ in range(global_provider.random.randint(3, 4)):
            AllocationFactory(request=request, cluster=global_provider.random.choice(clusters))

@transaction.atomic
def gen_comments_for_request(request, members, staff_users, n_comments=10):
    """Generate comments for a given allocation request."""
    for _ in range(n_comments):
        possible_authors = members + staff_users
        author = global_provider.random.choice(possible_authors)
        CommentFactory(
            request=request,
            user=author,
            private=author.is_staff and global_provider.random.choice([True, False])
        )


class Command(BaseCommand):
    help = "Generate seed data for testing purposes."

    def add_arguments(self, parser):
        parser.add_argument('--seed', type=int, help='Seed for random number generators', default=42)
        parser.add_argument('--n_users', type=int, help='Number of non-admin users to create', default=400)
        parser.add_argument('--n_staff_users', type=int, help='Number of admin users to create', default=100)
        parser.add_argument('--n_teams', type=int, help='Number of teams to create', default=200)
        parser.add_argument('--n_publications_per_team', type=int, help='Publications per team', default=10)
        parser.add_argument('--n_grants_per_team', type=int, help='Grants per team', default=10)
        parser.add_argument('--n_clusters', type=int, help='Number of clusters to create', default=5)
        parser.add_argument('--n_allocation_requests_per_team', type=int, help='Allocation requests per team', default=10)
        parser.add_argument('--n_comments_per_request', type=int, help='Comments per allocation request', default=10)
        parser.add_argument('--n_notifications_per_user', type=int, help='Notifications per user', default=15)

    def handle(self, *args, **options):
        seed = options['seed']
        n_users = options['n_users']
        n_staff_users = options['n_staff_users']
        n_teams = options['n_teams']
        n_publications_per_team = options['n_publications_per_team']
        n_grants_per_team = options['n_grants_per_team']
        n_clusters = options['n_clusters']
        n_allocation_requests_per_team = options['n_allocation_requests_per_team']
        n_comments_per_request = options['n_comments_per_request']
        n_notifications_per_user = options['n_notifications_per_user']

        if seed is not None:
            self.stdout.write(self.style.WARNING(f"Using seed: {seed}"))
            global_provider.reconfigure(seed)

        self.stdout.write(self.style.SUCCESS("Seeding data..."))

        users = list(UserFactory.create_batch(n_users, is_staff=False))
        staff_users = list(UserFactory.create_batch(n_staff_users, is_staff=True))
        all_users = users + staff_users

        self.stdout.write(f"✓ Created {n_users} users and {n_staff_users} staff users")

        teams = []
        for _ in tqdm(range(n_teams), desc="Creating teams and assigning members"):
            team, member_users = gen_team(all_users)
            teams.append((team, member_users))

        self.stdout.write(f"✓ Created {n_teams} teams and assigned members")

        for team, _ in tqdm(teams, desc="Creating publications and grants"):
            with transaction.atomic():
                PublicationFactory.create_batch(n_publications_per_team, team=team)
                GrantFactory.create_batch(n_grants_per_team, team=team)

        self.stdout.write("✓ Created publications and grants")

        clusters = ClusterFactory.create_batch(n_clusters)
        self.stdout.write(f"✓ Created {n_clusters} clusters")

        for team, members in tqdm(teams, desc="Creating allocation requests and allocations"):
            gen_alloc_req_for_team(team, members, staff_users, clusters, n_allocation_requests_per_team)

        self.stdout.write("✓ Created allocation requests and allocations")

        for team, members in tqdm(teams, desc="Creating comments"):
            for request in AllocationRequest.objects.filter(team=team):
                gen_comments_for_request(request, members, staff_users, n_comments_per_request)

        self.stdout.write(f"✓ Created {n_comments_per_request} comments per allocation request")

        for user in tqdm(all_users, desc="Creating notification preferences"):
            PreferenceFactory.create(user=user)

        self.stdout.write("✓ Created notification preferences")

        for user in tqdm(all_users, desc="Creating notifications"):
            NotificationFactory.create_batch(n_notifications_per_user, user=user)

        self.stdout.write(self.style.SUCCESS("✓ Seeded all data successfully!"))
