"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import logging

from celery import shared_task

from apps.allocations.models import Allocation, AllocationRequest
from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification_template
from apps.users.models import User

__all__ = [
    'notify_allocation_past_expiration',
    'notify_allocation_upcoming_expiration',

]

log = logging.getLogger(__name__)


@shared_task()
def notify_allocation_past_expiration(
    user: User,
    request: AllocationRequest,
    allocations: list[Allocation],
    save=True
) -> None:
    """Send a notification to alert a user their allocation request has expired.

    When persisting the notification record to the database, the allocation request
    ID is saved as notification metadata.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.
        allocations: The allocated resources tied to the request.
        save: Whether to save the notification to the application database.
    """

    log.info(f'Sending notification to user "{user.username}" on expiration of request {request.id}.')

    context = {
        'user_name': user.username,
        'user_first': user.first_name,
        'user_last': user.last_name,
        'req_id': request.id,
        'req_title': request.title,
        'req_team': request.team.name,
        'req_active': request.active,
        'req_expire': request.expire,
        'req_submitted': request.submitted,
        'allocations': [
            {
                'alloc_cluster': alloc.cluster.name,
                'alloc_requested': alloc.requested or 0,
                'alloc_awarded': alloc.awarded or 0,
                'alloc_final': alloc.final or 0,
            }
            for alloc in allocations
        ]
    }

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{request.id} has expired',
        template='past_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expired,
        notification_metadata={
            'request_id': request.id
        },
        save=save
    )


@shared_task()
def notify_allocation_upcoming_expiration(
    user: User,
    request: AllocationRequest,
    allocations: list[Allocation],
    save=True
) -> None:
    """Send a notification to alert a user their allocation request will expire soon.

    When persisting the notification record to the database, the allocation request
    ID and the days remaining until the expiration date are saved as notification metadata.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.
        allocations: The allocated resources tied to the request.
        save: Whether to save the notification to the application database.
    """

    log.info(f'Sending notification to user "{user.username}" on upcoming expiration for request {request.id}.')

    days_until_expire = request.get_days_until_expire()
    context = {
        'user_name': user.username,
        'user_first': user.first_name,
        'user_last': user.last_name,
        'req_id': request.id,
        'req_title': request.title,
        'req_team': request.team.name,
        'req_active': request.active,
        'req_expire': request.expire,
        'req_submitted': request.submitted,
        'req_days_left': days_until_expire,
        'allocations': [
            {
                'alloc_cluster': alloc.cluster.name,
                'alloc_requested': alloc.requested or 0,
                'alloc_awarded': alloc.awarded or 0,
            }
            for alloc in allocations
        ]
    }

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{request.id} is expiring soon',
        template='upcoming_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expiring,
        notification_metadata={
            'request_id': request.id,
            'days_to_expire': days_until_expire
        },
        save=save
    )
