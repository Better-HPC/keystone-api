"""Custom checks for validating system configurations and dependencies.

This module defines validation checks to ensure the proper configuration and
functionality of system components. Checks are automatically executed during
system initialization to ensure that all necessary conditions are met for
the system to operate correctly.
"""

import importlib

from django.core.checks import Error

from .celery import celery_app

__all__ = ['check_celery_beat_configuration']


def check_celery_beat_configuration(*args, **kwargs) -> list[Error]:
    """Verify all Celery Beat tasks are correctly registered with Celery."""

    errors = []
    beat_schedule = celery_app.conf.beat_schedule

    for task_name, task_info in beat_schedule.items():
        module_spec, obj_spec = task_info['task'].rsplit('.', maxsplit=1)

        try:
            module = importlib.import_module(module_spec)
            obj = getattr(module, obj_spec)

        # Make sure the task points to a module that exists
        except ModuleNotFoundError:
            errors.append(
                Error(
                    msg=f"Could not import module '{module_spec}'.",
                    hint="Double check the task definition in the Celery Beat configuration.",
                    obj=celery_app,
                    id="apps.scheduler.E001",
                )
            )

        # Make sure the task points to a member of the module that exists
        except AttributeError:
            errors.append(
                Error(
                    msg=f"Could not find attribute '{obj_spec}' in module '{module_spec}'.",
                    hint="Double check the task definition in the Celery Beat configuration.",
                    obj=celery_app,
                    id="apps.scheduler.E002",
                )
            )

        # Make sure the task is importable by Celery
        else:
            if not obj.__module__ == module.__name__:
                errors.append(
                    Error(
                        msg=f"Module '{module_spec}' is not absolute.",
                        hint=f"Use the module definition {obj.__module__}.",
                        obj=celery_app,
                        id="apps.scheduler.E003",
                    )
                )

    return errors
