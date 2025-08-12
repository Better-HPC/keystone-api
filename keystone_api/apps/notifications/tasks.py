"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import logging
from datetime import date, timedelta

from celery import shared_task

from apps.allocations.models import Allocation, AllocationRequest
from apps.users.models import User
from .models import Notification, Preference
from .shortcuts import send_notification_template

__all__ = [
    'notify_past_expirations',
    'notify_upcoming_expirations',
    'send_past_expiration_notice',
    'send_upcoming_expiration_notice',

]

log = logging.getLogger(__name__)


@shared_task()
def notify_upcoming_expirations() -> None:
    """Send a notification to all users with soon-to-expire allocations."""

    # Retrieve all approved allocation requests that expire in the future
    active_requests = AllocationRequest.objects.filter(
        status=AllocationRequest.StatusChoices.APPROVED,
        expire__gt=date.today()
    ).all()

    for request in active_requests:
        allocations = request.allocation_set.all()
        team_members = request.team.get_all_members().filter(is_active=True)

        for user in team_members:
            user_preferences = Preference.get_user_preference(user)
            should_notify = user_preferences.should_notify_upcoming_expiration(request_id=request.id, expire_date=request.expire)

            if should_notify:
                send_upcoming_expiration_notice.delay(user, request, allocations)


@shared_task()
def send_upcoming_expiration_notice(
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

    days_until_expire = (request.expire - date.today()).days if request.expire else None
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


@shared_task()
def notify_past_expirations() -> None:
    """Send a notification to all users with expired allocations."""

    # Retrieve all allocation requests that expired within the last three days
    active_requests = AllocationRequest.objects.filter(
        status=AllocationRequest.StatusChoices.APPROVED,
        expire__lte=date.today(),
        expire__gt=date.today() - timedelta(days=3),
    ).all()

    for request in active_requests:
        allocations = request.allocation_set.all()
        team_members = request.team.get_all_members().filter(is_active=True)

        for user in team_members:
            user_preferences = Preference.get_user_preference(user)
            should_notify = user_preferences.should_notify_past_expiration(request_id=request.id)

            if should_notify:
                send_past_expiration_notice.delay(user, request, allocations)


@shared_task()
def send_past_expiration_notice(
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
