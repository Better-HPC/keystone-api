"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.users.factories import TeamFactory
from .models import *

fake = Faker()


class GrantFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Grant` model."""

    class Meta:
        model = Grant

    title = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    agency = factory.LazyFunction(lambda: fake.company())
    amount = factory.LazyFunction(lambda: fake.pydecimal(left_digits=8, right_digits=2, positive=True))
    grant_number = factory.Sequence(lambda n: f"GRANT-{n:05d}")
    fiscal_year = factory.LazyFunction(lambda: fake.year())
    start_date = factory.LazyFunction(lambda: fake.date_this_decade())
    end_date = factory.LazyAttribute(lambda obj: fake.date_between_dates(date_start=obj.start_date, date_end=None))
    team = factory.SubFactory(TeamFactory)


class PublicationFactory(DjangoModelFactory):
    """Factory for creating test instances of a `Publication` model."""

    class Meta:
        model = Publication

    title = factory.LazyFunction(lambda: fake.sentence(nb_words=6))
    abstract = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=5))
    published = factory.LazyFunction(lambda: fake.date_between(start_date="-2y", end_date="today"))
    submitted = factory.LazyFunction(lambda: fake.date_between(start_date="-3y", end_date="today"))
    journal = factory.LazyFunction(lambda: fake.catch_phrase())
    doi = factory.Sequence(lambda n: f"10.1234/abcde{n}")
    preparation = factory.LazyFunction(lambda: fake.boolean(chance_of_getting_true=20))
    volume = factory.LazyFunction(lambda: fake.numerify(text="##"))
    issue = factory.LazyFunction(lambda: fake.numerify(text="#"))
    team = factory.SubFactory(TeamFactory)
