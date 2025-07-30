"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory
from factory.random import randgen

from apps.users.factories import TeamFactory
from .models import *

__all__ = ['GrantFactory', 'PublicationFactory']


class GrantFactory(DjangoModelFactory):
    """Factory for creating mock `Grant` instances.

    Generates grants with start dates between today and 5 years ago.
    End dates are generated between one and three years following the start date.
    """

    class Meta:
        """Factory settings."""

        model = Grant

    title = factory.Faker('sentence', nb_words=6)
    agency = factory.Faker('company')
    amount = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    grant_number = factory.Sequence(lambda n: f"GRANT-{n + 1:05d}")
    fiscal_year = factory.LazyAttribute(lambda obj: obj.start_date.year)
    start_date = factory.Faker('date_this_decade')

    team = factory.SubFactory(TeamFactory)

    @factory.lazy_attribute
    def end_date(self: Grant) -> date:
        """Generate the grant end date.

        Returns:
            A date within 1 to 3 years from the grant start.
        """

        duration_years = randgen.randint(1, 3)
        duration_days = timedelta(days=duration_years * 365)
        return self.start_date + duration_days


class PublicationFactory(DjangoModelFactory):
    """Factory for creating mock `Publication` instances.

    Publications have a 20% chance of being in preparation, resulting in
    no `submitted` or `published` date being set on the record. If a publication
    is not in preparation, it is assigned a random submitted date within the
    past five years. Submitted applications have an 85% chance of being published,
    with a published date falling 20 to 60 days after submission.
    """

    class Meta:
        """Factory settings."""

        model = Publication

    title = factory.Faker("sentence", nb_words=6)
    abstract = factory.Faker("paragraph", nb_sentences=5)
    journal = factory.Faker("catch_phrase")
    doi = factory.Faker('doi')
    preparation = factory.Faker("pybool", truth_probability=20)

    team = factory.SubFactory(TeamFactory)

    @factory.lazy_attribute
    def submitted(self: Publication) -> date | None:
        """Generate a random submission date.

        Returns `None` for publications still in preparation. Otherwise,
        returns a random date within the last five years that is at least
        two months prior to today. This leave room for time between the
        `submitted` and `published` dates.
        """

        five_years_in_days = 365 * 5
        if not self.preparation:
            days = randgen.randint(60, five_years_in_days)
            return date.today() - timedelta(days=days)

    @factory.lazy_attribute
    def published(self: Publication) -> date | None:
        """Generate a random publication date.

        Submitted publications have an 85% chance of returning a random date
        within 30 days after the `submitted` date. Otherwise, returns `None`.
        """

        if self.submitted and randgen.random() < 0.85:
            return self.submitted + timedelta(days=randgen.randint(20, 60))

    @factory.lazy_attribute
    def volume(self: Publication) -> str | None:
        """Generate a random volume number.

        Returns `None` for unpublished records and a random integer otherwise.
        """

        if self.published:
            return f'{randgen.randint(1, 20):02}'

    @factory.lazy_attribute
    def issue(self: Publication) -> str | None:
        """Generate a random issue number.

        Returns `None` for unpublished records and a random integer otherwise.
        """

        if self.published:
            return f'{randgen.randint(1, 9)}'
