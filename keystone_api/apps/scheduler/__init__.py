from .celery import celery_app

# The `celery_app` variable must be defined here to be discovered by Celery workers
__all__ = ["celery_app"]
