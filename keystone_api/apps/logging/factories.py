"""Factories for creating mock database records.

Factory classes are used to generate realistic mock data for use in
testing and development. Each class encapsulates logic for constructing
a specific model instance with sensible default values. This streamlines
the creation of mock data, avoiding the need for hardcoded or repetitive
setup logic.
"""

import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory

from apps.users.factories import UserFactory
from .models import *

__all__ = [
    'AuditLogFactory',
    'RequestLogFactory',
    'TaskResultFactory',
]


class AuditLogFactory(DjangoModelFactory):
    """Factory for creating mock `AuditLog` instances."""

    class Meta:
        """Factory settings."""

        model = AuditLog

    content_type = factory.LazyFunction(
        lambda: ContentType.objects.get_for_model(AuditLog)
    )
    object_pk = factory.Sequence(lambda n: str(n + 1))
    object_repr = factory.Faker('sentence', nb_words=4)
    action = AuditLog.Action.UPDATE
    changes = factory.LazyFunction(dict)
    actor = factory.SubFactory(UserFactory)


class RequestLogFactory(DjangoModelFactory):
    """Factory for creating mock `RequestLog` instances."""

    class Meta:
        """Factory settings."""

        model = RequestLog

    method = factory.Iterator(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
    endpoint = factory.Faker('uri_path')
    response_code = 200
    remote_address = factory.Faker('ipv4')
    cid = factory.Faker('uuid4')
    user = factory.SubFactory(UserFactory)


class TaskResultFactory(DjangoModelFactory):
    """Factory for creating mock `TaskResult` instances."""

    class Meta:
        """Factory settings."""

        model = TaskResult

    task_id = factory.Faker('uuid4')
    task_name = factory.Faker('slug')
    status = 'SUCCESS'
    result = factory.LazyFunction(dict)
