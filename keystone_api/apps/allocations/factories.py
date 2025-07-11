"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import timedelta
from django.utils import timezone
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import *
from apps.research_products.models import Grant, Publication
from apps.factories.providers import global_provider
from apps.users.factories import UserFactory, TeamFactory
from apps.research_products.factories import GrantFactory, PublicationFactory

class ClusterFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Cluster` model."""

    class Meta:
        model = Cluster

    name = factory.Sequence(lambda n: f"cluster{n}")
    description = global_provider.fake.sentence()
    enabled = True

class AllocationRequestFactory(DjangoModelFactory):
    """Factory for creating test instances of an `AllocationRequest` model."""

    class Meta:
        model = AllocationRequest

    title = factory.LazyFunction(lambda: global_provider.fake.sentence(nb_words=4))
    description = factory.LazyFunction(lambda: global_provider.fake.text(max_nb_chars=2000))
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
    """Factory for creating test instances of an `Allocation` model."""

    class Meta:
        model = Allocation

    requested = factory.LazyFunction(lambda: global_provider.fake.pyint(min_value=1000, max_value=100000))
    awarded = factory.LazyFunction(lambda: global_provider.fake.pyint(min_value=500, max_value=100000))
    final = factory.LazyFunction(lambda: global_provider.fake.pyint(min_value=500, max_value=100000))
    cluster = factory.SubFactory(ClusterFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class AllocationReviewFactory(DjangoModelFactory):
    """Factory for creating test instances of an `AllocationReview` model."""

    class Meta:
        model = AllocationReview

    status = fuzzy.FuzzyChoice(AllocationReview.StatusChoices.values)
    request = factory.SubFactory(AllocationRequestFactory)
    reviewer = factory.SubFactory(UserFactory)


class AttachmentFactory(DjangoModelFactory):
    """Factory for creating test instances of an `Attachment` model."""

    class Meta:
        model = Attachment

    file = factory.django.FileField(filename="document.pdf")
    name = factory.LazyAttribute(lambda o: o.file.name)
    request = factory.SubFactory(AllocationRequestFactory)


class CommentFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Comment` model."""

    class Meta:
        model = Comment

    content = factory.LazyFunction(lambda: global_provider.fake.sentence(nb_words=10))
    private = factory.LazyFunction(lambda: global_provider.fake.boolean(chance_of_getting_true=30))
    user = factory.SubFactory(UserFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class JobStatsFactory(DjangoModelFactory):
    """Factory for creating test instances of a `JobStats` model."""
    class Meta:
        model = JobStats

    jobid = factory.Sequence(lambda n: f"job{n}")
    jobname =factory.LazyFunction(lambda:  global_provider.fake.word())
    state = fuzzy.FuzzyChoice(["RUNNING", "COMPLETED", "FAILED"])
    submit = factory.LazyFunction(timezone.now)
    start = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=1))
    end = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=10))
    team = factory.SubFactory(TeamFactory)
    cluster = factory.SubFactory(ClusterFactory)
