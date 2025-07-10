"""Factories for the allocations app, used for generating test data.
These factories create instances of models related to allocation requests, allocations, reviews, attachments, comments, and job statistics.
"""

import random
from datetime import timedelta
from django.utils import timezone
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from apps.allocations.models import (
    Allocation,
    AllocationRequest,
    AllocationReview,
    Attachment,
    Cluster,
    Comment,
    JobStats,
)
from apps.research_products.models import Grant, Publication

from apps.users.factories import UserFactory, TeamFactory
from apps.research_products.factories import GrantFactory, PublicationFactory

class ClusterFactory(DjangoModelFactory):
    """Factory for creating test instances of a Cluster model."""

    class Meta:
        model = Cluster

    name = factory.Sequence(lambda n: f"cluster{n}")
    description = factory.Faker("sentence")
    enabled = True

class AllocationRequestFactory(DjangoModelFactory):
    """Factory for creating test instances of an AllocationRequest model."""

    class Meta:
        model = AllocationRequest

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("text", max_nb_chars=2000)
    submitted = factory.LazyFunction(timezone.now)
    active = factory.LazyFunction(lambda: timezone.now().date())
    expire = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=90))
    status = fuzzy.FuzzyChoice(AllocationRequest.StatusChoices.values)
    submitter = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)

    @factory.post_generation
    def assignees(self, create, extracted, **kwargs):
        if create and extracted:
            self.assignees.set(extracted)

    @factory.post_generation
    def publications(self, create, extracted, **kwargs):
        if create and extracted:
            self.publications.set(extracted)

    @factory.post_generation
    def grants(self, create, extracted, **kwargs):
        if create and extracted:
            self.grants.set(extracted)


class AllocationFactory(DjangoModelFactory):
    """Factory for creating test instances of an Allocation model."""

    class Meta:
        model = Allocation

    requested = factory.Faker("pyint", min_value=1000, max_value=100000)
    awarded = factory.Faker("pyint", min_value=500, max_value=100000)
    final = factory.Faker("pyint", min_value=500, max_value=100000)
    cluster = factory.SubFactory(ClusterFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class AllocationReviewFactory(DjangoModelFactory):
    """Factory for creating test instances of an AllocationReview model."""

    class Meta:
        model = AllocationReview

    status = fuzzy.FuzzyChoice(AllocationReview.StatusChoices.values)
    request = factory.SubFactory(AllocationRequestFactory)
    reviewer = factory.SubFactory(UserFactory)


class AttachmentFactory(DjangoModelFactory):
    """Factory for creating test instances of an Attachment model."""

    class Meta:
        model = Attachment

    file = factory.django.FileField(filename="document.pdf")
    name = factory.LazyAttribute(lambda o: o.file.name)
    request = factory.SubFactory(AllocationRequestFactory)


class CommentFactory(DjangoModelFactory):
    """Factory for creating test instances of a Comment model."""

    class Meta:
        model = Comment

    content = factory.Faker("sentence")
    private = factory.Faker("boolean", chance_of_getting_true=30)
    user = factory.SubFactory(UserFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class JobStatsFactory(DjangoModelFactory):
    """Factory for creating test instances of a JobStats model."""
    class Meta:
        model = JobStats

    jobid = factory.Sequence(lambda n: f"job{n}")
    jobname = factory.Faker("word")
    state = fuzzy.FuzzyChoice(["RUNNING", "COMPLETED", "FAILED"])
    submit = factory.LazyFunction(timezone.now)
    start = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=1))
    end = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=10))
    team = factory.SubFactory(TeamFactory)
    cluster = factory.SubFactory(ClusterFactory)
