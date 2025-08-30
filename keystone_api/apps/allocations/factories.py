"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import date, timedelta

import factory
from django.utils import timezone
from factory import LazyFunction
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

    name = factory.Sequence(lambda n: f"Cluster {n + 1}")
    description = factory.Faker('sentence')
    enabled = True


class AllocationRequestFactory(DjangoModelFactory):
    """Factory for creating mock `AllocationRequest` instances.

    Generates an allocation request submitted within the past five years.
    """

    class Meta:
        """Factory settings."""

        model = AllocationRequest

    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=2000)
    submitted = factory.Faker('date_time_between', start_date="-5y", end_date="now", tzinfo=timezone.get_default_timezone())

    submitter = factory.SubFactory(UserFactory)
    team = factory.SubFactory(TeamFactory)

    @factory.lazy_attribute
    def status(self: AllocationRequest) -> AllocationRequest.StatusChoices:
        """Randomly generate an allocation request status value.

        Allocation requests submitted within the last two weeks are set to
        either `PENDING`, `APPROVED`, or `DECLINED`. Older allocation requests
        are either `APPROVED`, or `DECLINED`.
        """

        two_weeks_ago = timezone.now() - timedelta(weeks=2)
        if self.submitted >= two_weeks_ago:
            weights = [60, 30, 10]
            status_choices = (
                AllocationRequest.StatusChoices.PENDING,
                AllocationRequest.StatusChoices.APPROVED,
                AllocationRequest.StatusChoices.DECLINED,
            )

        else:
            weights = [90, 10]
            status_choices = (
                AllocationRequest.StatusChoices.APPROVED,
                AllocationRequest.StatusChoices.DECLINED
            )

        return randgen.choices(
            population=status_choices,
            weights=weights,
            k=1
        )[0]

    @factory.lazy_attribute
    def active(self: AllocationRequest) -> date | None:
        """Generate the request active date.

        For approved allocation requests, the active date is set to a random
        value between one and ten days after the submission date. For all
        other requests, `None` is returned.
        """

        if self.status == AllocationRequest.StatusChoices.APPROVED:
            days_spent_pending = randgen.randint(1, 10)
            return self.submitted.date() + timedelta(days=days_spent_pending)

        return None

    @factory.lazy_attribute
    def expire(self: AllocationRequest) -> date | None:
        """Generate the request active date.

        For approved allocation requests, the expiration date is set to one
        year after the active date. For all other requests, `None` is returned.
        """

        if self.active:
            return self.active + timedelta(days=365)

        return None

    @factory.post_generation
    def assignees(self: AllocationRequest, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `assignees` relationship."""

        if create and extracted:
            self.assignees.set(extracted)

    @factory.post_generation
    def publications(self: AllocationRequest, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `publications` relationship."""

        if create and extracted:
            self.publications.set(extracted)

    @factory.post_generation
    def grants(self: AllocationRequest, create: bool, extracted: list[User] | None, **kwargs):
        """Populate the many-to-many `grants` relationship."""

        if create and extracted:
            self.grants.set(extracted)


class AllocationFactory(DjangoModelFactory):
    """Factory for creating mock `Allocation` instances."""

    class Meta:
        """Factory settings."""

        model = Allocation

    requested = factory.Faker('pyint', min_value=1000, max_value=100000)

    cluster = factory.SubFactory(ClusterFactory)
    request = factory.SubFactory(AllocationRequestFactory)

    @factory.lazy_attribute
    def awarded(self: Allocation) -> int | None:
        """Generate a number of awarded service units.

        Defaults to `None` for allocations attached to unapproved allocation requests.
        Otherwise, generates a value less than or equal to the requested service units.
        """

        is_approved = self.request.status == AllocationRequest.StatusChoices.APPROVED
        if is_approved:
            return randgen.randint(0, self.requested // 100) * 100

    @factory.lazy_attribute
    def final(self: Allocation) -> int | None:
        """Generate a number of final utilized service units.

        Returns `None` for allocations attached to unexpired allocation requests.
        Otherwise, generates a value less than or equal to the awarded service units.
        """

        is_approved = self.request.status == AllocationRequest.StatusChoices.APPROVED
        if not is_approved:
            return None

        is_expired = (self.request.expire is not None) and (self.request.expire <= date.today())
        if is_approved and is_expired:
            return randgen.randint(0, self.awarded // 100) * 100


class AllocationReviewFactory(DjangoModelFactory):
    """Factory for creating mock `AllocationReview` instances."""

    class Meta:
        """Factory settings."""

        model = AllocationReview

    status = LazyFunction(lambda: randgen.choice(AllocationReview.StatusChoices.values))

    request = factory.SubFactory(AllocationRequestFactory)
    reviewer = factory.SubFactory(UserFactory, is_staff=True)

    @factory.lazy_attribute
    def submitted(self) -> date:
        """Generates a submission date between the request's submitted and active dates.

        If the request has no active date, the upper bound is today.
        The result is always on or after the request's submitted date, and never in the future.
        """

        # Determine number of integer days between request submission and activation
        request_submitted_date = self.request.submitted.date()
        request_active_date = min(self.request.active or date.today(), date.today())
        delta = request_active_date - request_submitted_date

        # Return the request submission datetime plus a random number of days
        delta_days = randgen.randint(0, max(delta.days, 0))
        return self.request.submitted + timedelta(days=delta_days)


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

    user = factory.SubFactory(UserFactory)
    request = factory.SubFactory(AllocationRequestFactory)


class JobStatsFactory(DjangoModelFactory):
    """Factory for creating mock `JobStats` instances."""

    class Meta:
        """Factory settings."""

        model = JobStats

    jobid = factory.Sequence(lambda n: f"{n + 1}")
    jobname = factory.Faker('word')
    state = LazyFunction(lambda: randgen.choice(["PENDING", "RUNNING", "COMPLETED", "FAILED"]))
    submit = factory.Faker('date_time_between', start_date='-5y', end_date='now', tzinfo=timezone.get_default_timezone())
    start = factory.LazyAttribute(lambda obj: obj.submit + timedelta(hours=randgen.randint(1, 60)))
    end = factory.LazyAttribute(lambda obj: obj.start + timedelta(minutes=randgen.randint(25, 300)))

    team = factory.SubFactory(TeamFactory)
    cluster = factory.SubFactory(ClusterFactory)
