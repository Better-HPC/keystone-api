"""Application interface for the backend Celery service.

Defines a specially named `celery_app` variable which acts as the primary
interface between Django and Celery. Celery tasks are automatically registered
with the Celery application instance for all applications defined in the
`settings.INSTALLED_APPS` list.
"""

from celery import Celery
from celery.schedules import crontab

celery_app = Celery('scheduler')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    'apps.users.tasks.ldap_update_users': {
        'task': 'apps.users.tasks.ldap_update_users',
        'schedule': crontab(minute='*/15'),
        'description': 'This task synchronizes user data against LDAP. This task does nothing if LDAP is disabled.'
    },
    'apps.logging.tasks.clear_log_files': {
        'task': 'apps.logging.tasks.clear_log_files',
        'schedule': crontab(hour='0', minute='0'),
        'description': 'This task deletes old log entries according to application settings.'
    },
    'apps.allocations.tasks.limits.update_limits': {
        'task': 'apps.allocations.tasks.limits.update_limits',
        'schedule': crontab(minute='0'),
        'description': 'This task updates all Slurm clusters with the latest user allocation limits.'
    },
    'apps.allocations.tasks.notifications.notify_upcoming_expirations': {
        'task': 'apps.allocations.tasks.notifications.notify_upcoming_expirations',
        'schedule': crontab(hour='0', minute='0'),
        'description': 'This task issues notifications informing users of upcoming expirations.'
    },
    'apps.allocations.tasks.notifications.notify_past_expirations': {
        'task': 'apps.allocations.tasks.notifications.notify_past_expirations',
        'schedule': crontab(hour='0', minute='0'),
        'description': 'This task issues notifications informing users when their allocations have expired.'
    },
}
