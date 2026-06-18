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
    "AuditLogFactory",
    "RequestLogFactory",
    "TaskResultFactory",
]


class AuditLogFactory(DjangoModelFactory):
    """Factory for creating mock `AuditLog` instances."""

    class Meta:
        """Factory settings."""

        model = AuditLog

    content_type = factory.LazyFunction(lambda: ContentType.objects.get_for_model(AuditLog))
    object_pk = factory.Sequence(lambda n: str(n + 1))
    object_repr = factory.Faker("sentence", nb_words=4)
    action = AuditLog.Action.UPDATE
    changes = factory.LazyFunction(dict)
    actor = factory.SubFactory(UserFactory)


class RequestLogFactory(DjangoModelFactory):
    """Factory for creating mock `RequestLog` instances."""

    class Meta:
        """Factory settings."""

        model = RequestLog

    method = factory.Iterator(["GET", "POST", "PUT", "PATCH", "DELETE"])
    endpoint = factory.Faker("uri_path")
    response_code = 200
    remote_address = factory.Faker("ipv4")
    cid = factory.Faker("uuid4")
    user = factory.SubFactory(UserFactory)


class TaskResultFactory(DjangoModelFactory):
    """Factory for creating mock `TaskResult` instances."""

    class Meta:
        """Factory settings."""

        model = TaskResult

    task_id = factory.Faker("uuid4")
    task_name = factory.Faker("slug")
    status = "SUCCESS"
    result = factory.LazyFunction(dict)

    {"task_id": "054ed313-17b0-4c46-b1cd-1e53c2a0dd42", "task_name": "apps.allocations.tasks.limits.update_limits_for_cluster", "task_args": "\"('mpi',)\"","task_kwargs": "\"{}\"","status": "FAILURE","worker": "w2@api.keystone.crcd.pitt.edu","content_type": "application/json","content_encoding": "utf-8","result": "{\"exc_type\": \"RuntimeError\", \"exc_message\": [\"Error executing shell command: sacctmgr show -nP account withassoc where parents=root format=Account cluster=mpi \\n sacctmgr: error: _open_persist_conn: failed to open persistent connection to host:db.crc.pitt.edu:6819: Connection refused\\nsacctmgr: error: Sending PersistInit msg: Connection refused\"], \"exc_module\": \"builtins\"}", "date_created": "2026-06-16T10:00:00.105284-04:00", "date_started": None, "date_done": "2026-06-16T10:00:00.105311-04:00","traceback": "Traceback (most recent call last):\n  File \"/home/keystone/.local/share/pipx/venvs/keystone-api/lib64/python3.11/site-packages/celery/app/trace.py\", line 453, in trace_task\n    R = retval = fun(*args, **kwargs)\n                 ^^^^^^^^^^^^^^^^^^^^\n  File \"/home/keystone/.local/share/pipx/venvs/keystone-api/lib64/python3.11/site-packages/celery/app/trace.py\", line 736, in __protected_call__\n    return self.run(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/keystone/.local/share/pipx/venvs/keystone-api/lib/python3.11/site-packages/keystone_api/apps/allocations/tasks/limits.py\", line 43, in update_limits_for_cluster\n    slurm_accounts = slurm.get_slurm_account_names(cluster.name)\n                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/keystone/.local/share/pipx/venvs/keystone-api/lib/python3.11/site-packages/keystone_api/plugins/slurm.py\", line 114, in get_slurm_account_names\n    return set(subprocess_call(cmd).split())\n               ^^^^^^^^^^^^^^^^^^^^\n  File \"/home/keystone/.local/share/pipx/venvs/keystone-api/lib/python3.11/site-packages/keystone_api/plugins/slurm.py\", line 95, in subprocess_call\n    raise RuntimeError(message)\nRuntimeError: Error executing shell command: sacctmgr show -nP account withassoc where parents=root format=Account cluster=mpi \n sacctmgr: error: _open_persist_conn: failed to open persistent connection to host:db.crc.pitt.edu:6819: Connection refused\nsacctmgr: error: Sending PersistInit msg: Connection refused\n","meta": "{\"children\": []}"}