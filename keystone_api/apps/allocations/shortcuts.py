"""Helper functions for streamlining common tasks.

Shortcuts are designed to simplify common tasks such as rendering templates,
redirecting URLs, issuing notifications, and handling HTTP responses.
"""

import logging

from apps.allocations.models import AllocationRequest
from apps.notifications.models import Notification
from apps.notifications.shortcuts import send_notification_template
from apps.users.models import User

log = logging.getLogger(__name__)


def _build_allocation_context(request: AllocationRequest):
    """Construct a context dictionary with the details of an allocation request.

    Args:
        request: The allocation request to extract context from.

    Returns:
        A dictionary containing key metadata about the allocation request.
    """

    return {
        'team_name': request.team.name,
        'request_title': request.title,
        'request_submitted': request.submitted,
        'request_active': request.active,
        'request_expire': request.expire,
    }


def send_notification_upcoming_expiration(user: User, request: AllocationRequest, save=True) -> None:
    """Send a notification to alert a user their allocation request will expire soon.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.
        save: Whether to save the notification to the application database.
    """

    log.debug(f'Sending notification to user "{user.username}" on upcoming expiration for request {request.id}.')

    days_until_expire = request.get_days_until_expire()
    send_notification_template(
        user=user,
        subject=f'You have an allocation expiring on {request.expire}',
        template='upcoming_expiration.html',
        context={
            'user_username': user.username,
            'user_first': user.first_name,
            'user_last': user.last_name,
            'team_name': request.team.name,
            'days_to_expire': days_until_expire,
            **_build_allocation_context(request),
            'pending': [_build_allocation_context(req) for req in AllocationRequest.objects.pending_requests(team=request.team)],
            'active': [_build_allocation_context(req) for req in AllocationRequest.objects.active_requests(team=request.team)],
        },
        notification_type=Notification.NotificationType.request_expiring,
        notification_metadata={
            'request_id': request.id,
            'days_to_expire': days_until_expire
        },
        save=save
    )


def send_notification_past_expiration(user: User, request: AllocationRequest, save=True) -> None:
    """Send a notification to alert a user their allocation request has expired.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.
        save: Whether to save the notification to the application database.
    """

    log.debug(f'Sending notification to user "{user.username}" on expiration of request {request.id}.')

    send_notification_template(
        user=user,
        subject='One of your allocations has expired',
        template='past_expiration.html',
        context={
            'user_username': user.username,
            'user_first': user.first_name,
            'user_last': user.last_name,
            'team_name': request.team.name,
            **_build_allocation_context(request),
            'pending': [_build_allocation_context(req) for req in AllocationRequest.objects.pending_requests(team=request.team)],
            'active': [_build_allocation_context(req) for req in AllocationRequest.objects.active_requests(team=request.team)],
        },
        notification_type=Notification.NotificationType.request_expired,
        notification_metadata={
            'request_id': request.id
        },
        save=save
    )
