"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

from datetime import date, timedelta
from typing import cast

import factory
from factory.django import DjangoModelFactory
from factory.random import randgen

from apps.users.factories import TeamFactory
from .models import *

__all__ = ['GrantFactory', 'PublicationFactory']


class GrantFactory(DjangoModelFactory):
    """Factory for creating mock `Grant` instances."""

    class Meta:
        """Factory settings."""

        model = Grant

    title = factory.Faker('sentence', nb_words=6)
    agency = factory.Faker('company')
    amount = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    grant_number = factory.Sequence(lambda n: f"GRANT-{n:05d}")
    fiscal_year = factory.Faker('year')
    start_date = factory.Faker('date_this_decade')
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(randgen.randint(30, 730)))

    team = factory.SubFactory(TeamFactory)


class PublicationFactory(DjangoModelFactory):
    """Factory for creating mock `Publication` instances."""

    class Meta:
        """Factory settings."""

        model = Publication

    title = factory.Faker("sentence", nb_words=6)
    abstract = factory.Faker("paragraph", nb_sentences=5)
    journal = factory.Faker("catch_phrase")
    doi = factory.Faker('doi')
    preparation = factory.Faker("pybool", truth_probability=20)
    volume = factory.Faker("numerify", text="##")
    issue = factory.Faker("numerify", text="#")

    team = factory.SubFactory(TeamFactory)

    @factory.lazy_attribute
    def submitted(self) -> date | None:
        """Generate a random submission date.

        Returns `None` for publications still in preparation.
        """

        if self.preparation:
            return None

        return date.today() - timedelta(days=randgen.randint(0, 365 * 3))

    @factory.lazy_attribute
    def published(self) -> date | None:
        """Generate a random publication date.

        Returns `None` for publications still in preparation.
        """

        if self.preparation:
            return None

        submitted = cast(date, self.submitted)
        delta = (date.today() - submitted).days
        return submitted + timedelta(days=randgen.randint(0, delta))
