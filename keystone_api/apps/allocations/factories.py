"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.random import randgen

from apps.users.factories import TeamFactory, UserFactory
from apps.users.models import User
from .models import *

__all__ = [
    'AllocationFactory',
    'AllocationRequestFactory',
    'AllocationReviewFactory',
    'AttachmentFactory',
    'ClusterFactory',
    'CommentFactory',
    'JobStatsFactory'
]


class ClusterFactory(DjangoModelFactory):
    """Factory for creating mock `Cluster` instances."""

    class Meta:
        """Factory settings."""

        model = Cluster

    name = factory.Sequence(lambda n: f"Cluster {n}")
    description = factory.Faker('sentence')
    enabled = True


class AllocationRequestFactory(DjangoModelFactory):
    """Factory for creating mock `AllocationRequest` instances."""

    class Meta:
        """Factory settings."""

        model = AllocationRequest

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=2000)
    submitted = factory.LazyFunction(timezone.now)
    active = factory.LazyFunction(lambda: timezone.now().date())
    expire = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=90))
    status = randgen.choice(AllocationRequest.StatusChoices.values)

    submitter = factory.SubFactory(UserFactory, is_staff=False)
    team = factory.SubFactory(TeamFactory)

    @factory.post_generation
    def assignees(self, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `assignees` relationship."""

        if create and extracted:
            self.assignees.set(extracted)

    @factory.post_generation
    def publications(self, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `publications` relationship."""

        if create and extracted:
            self.publications.set(extracted)

    @factory.post_generation
    def grants(self, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `grants` relationship."""

        if create and extracted:
            self.grants.set(extracted)


class AllocationFactory(DjangoModelFactory):
    """Factory for creating mock `Allocation` instances."""

    class Meta:
        """Factory settings."""

        model = Allocation

    requested = factory.Faker('pyint', min_value=1000, max_value=100000)
    awarded = factory.Faker('pyint', min_value=500, max_value=100000)
    final = factory.Faker('pyint', min_value=500, max_value=100000)

    cluster = factory.SubFactory(ClusterFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class AllocationReviewFactory(DjangoModelFactory):
    """Factory for creating test instances of an `AllocationReview` model."""

    class Meta:
        """Factory settings."""

        model = AllocationReview

    status = randgen.choice(AllocationReview.StatusChoices.values)

    request = factory.SubFactory(AllocationRequestFactory)
    reviewer = factory.SubFactory(UserFactory, is_staff=False)


class AttachmentFactory(DjangoModelFactory):
    """Factory for creating mock `Attachment` instances."""

    class Meta:
        """Factory settings."""

        model = Attachment

    file = factory.django.FileField(filename="document.pdf")
    name = factory.LazyAttribute(lambda o: o.file.name)
    request = factory.SubFactory(AllocationRequestFactory)


class CommentFactory(DjangoModelFactory):
    """Factory for creating mock `Comment` instances."""

    class Meta:
        """Factory settings."""

        model = Comment

    content = factory.Faker('sentence', nb_words=10)
    private = factory.Faker('pybool', truth_probability=10)

    user = factory.SubFactory(UserFactory, is_staff=False)
    request = factory.SubFactory(AllocationRequestFactory)


class JobStatsFactory(DjangoModelFactory):
    """Factory for creating mock `JobStats` instances."""

    class Meta:
        """Factory settings."""

        model = JobStats

    jobid = factory.Sequence(lambda n: f"{n}")
    jobname = factory.Faker('word')
    state = randgen.choice(["RUNNING", "COMPLETED", "FAILED"])
    submit = factory.Faker('date_time_between', start_date='-1y', end_date='-1d')
    start = factory.LazyAttribute(lambda obj: obj.submit + timedelta(minutes=randgen.randint(1, 60)))
    end = factory.LazyAttribute(lambda obj: obj.start + timedelta(minutes=randgen.randint(5, 240)))

    team = factory.SubFactory(TeamFactory)
    cluster = factory.SubFactory(ClusterFactory)
