"""Factories for creating test data for research products like Grants and Publications.
These factories use the factory library to generate realistic data for testing purposes.
This module defines two factories: GrantFactory and PublicationFactory.
"""

import factory
from factory.django import DjangoModelFactory
from factory import fuzzy

from apps.research_products.models import Grant, Publication
from apps.users.factories import TeamFactory


class GrantFactory(DjangoModelFactory):
    """Factory for creating test instances of a Grant model."""

    class Meta:
        model = Grant

    title = factory.Faker("sentence", nb_words=6)
    agency = factory.Faker("company")
    amount = factory.Faker("pydecimal", left_digits=8, right_digits=2, positive=True)
    grant_number = factory.Sequence(lambda n: f"GRANT-{n:05d}")
    fiscal_year = factory.Faker("year")
    start_date = factory.Faker("date_this_decade")
    end_date = factory.Faker("date_between_dates", date_start=factory.SelfAttribute("..start_date"), date_end=None)
    team = factory.SubFactory(TeamFactory)


class PublicationFactory(DjangoModelFactory):
    """Factory for creating test instances of a Publication model."""

    class Meta:
        model = Publication

    title = factory.Faker("sentence", nb_words=6)
    abstract = factory.Faker("paragraph", nb_sentences=5)
    published = factory.Faker("date_between", start_date="-2y", end_date="today")
    submitted = factory.Faker("date_between", start_date="-3y", end_date="today")
    journal = factory.Faker("catch_phrase")
    doi = factory.Sequence(lambda n: f"10.1234/abcde{n}")
    preparation = factory.Faker("boolean", chance_of_getting_true=20)
    volume = factory.Faker("numerify", text="##")
    issue = factory.Faker("numerify", text="#")
    team = factory.SubFactory(TeamFactory)
