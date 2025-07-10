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

import random
import factory
from django.db import transaction
from django.core.management.base import BaseCommand
from faker import Faker
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

fake = Faker()


class Command(BaseCommand):
    help = "Generate seed data for testing purposes."

    def add_arguments(self, parser):
        parser.add_argument('--seed', type=int, help='Seed for random number generators', default=None)

    def handle(self, *args, **options):
        seed = options['seed']
        n_users = 400
        n_staff_users = 100
        n_teams = 200
        n_publications_per_team = 10
        n_grants_per_team = 10
        n_clusters = 5
        n_allocation_requests_per_team = 10
        n_comments_per_request = 10
        n_notifications_per_user = 15

        if seed is not None:
            self.stdout.write(self.style.WARNING(f"Using seed: {seed}"))
            factory.random.reseed_random(seed)
            random.seed(seed)
            Faker.seed(seed)

        self.stdout.write(self.style.SUCCESS("Seeding data..."))

        users = list(UserFactory.create_batch(n_users, is_staff=False))
        staff_users = list(UserFactory.create_batch(n_staff_users, is_staff=True))
        all_users = users + staff_users

        self.stdout.write(f"✓ Created {n_users} users and {n_staff_users} staff users")

        teams = []
        for _ in tqdm(range(n_teams), desc="Creating teams and assigning members"):
            with transaction.atomic():
                team = TeamFactory()
                member_users = random.sample(all_users, random.randint(3, 4))
                for user in member_users:
                    role = random.choice([r[0] for r in Membership.Role.choices])
                    MembershipFactory(user=user, team=team, role=role)
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
            with transaction.atomic():
                team_grants = list(Grant.objects.filter(team=team))
                team_publications = list(Publication.objects.filter(team=team))
                for _ in range(n_allocation_requests_per_team):
                    submitter = random.choice(members)
                    request = AllocationRequestFactory(team=team, submitter=submitter)

                    assignees = random.sample(staff_users, k=random.randint(1, min(2, len(staff_users))))
                    request.assignees.set(assignees)

                    if team_publications:
                        pubs = random.sample(team_publications, k=random.randint(1, min(2, len(team_publications))))
                        request.publications.set(pubs)

                    if team_grants:
                        grants = random.sample(team_grants, k=random.randint(1, min(2, len(team_grants))))
                        request.grants.set(grants)

                    for _ in range(random.randint(3, 4)):
                        AllocationFactory(request=request, cluster=random.choice(clusters))

        self.stdout.write("✓ Created allocation requests and allocations")

        for team, members in tqdm(teams, desc="Creating comments"):
            for request in AllocationRequest.objects.filter(team=team):
                with transaction.atomic():
                    for _ in range(n_comments_per_request):
                        possible_authors = members + staff_users
                        author = random.choice(possible_authors)
                        CommentFactory(
                            request=request,
                            user=author,
                            private=author.is_staff and random.choice([True, False])
                        )

        self.stdout.write(f"✓ Created {n_comments_per_request} comments per allocation request")

        for user in tqdm(all_users, desc="Creating notification preferences"):
            PreferenceFactory.create(user=user)

        self.stdout.write("✓ Created notification preferences")

        for user in tqdm(all_users, desc="Creating notifications"):
            NotificationFactory.create_batch(n_notifications_per_user, user=user)

        self.stdout.write(self.style.SUCCESS("✓ Seeded all data successfully!"))
