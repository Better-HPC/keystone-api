"""Background tasks for issuing user notifications."""

import logging
from datetime import date, timedelta

from celery import shared_task

from apps.allocations.models import AllocationRequest
from apps.notifications.models import Notification, Preference
from apps.notifications.tasks import notify_allocation_past_expiration, notify_allocation_upcoming_expiration
from apps.users.models import User

__all__ = [
    'notify_past_expirations',
    'notify_upcoming_expirations',
    'should_notify_past_expiration',
    'should_notify_upcoming_expiration'
]

log = logging.getLogger(__name__)


def should_notify_upcoming_expiration(user: User, request: AllocationRequest) -> bool:
    """Determine if a notification should be sent concerning the upcoming expiration of an allocation.

     Returns `True` if a notification is warranted by user preferences and
     an existing notification has not already been issued.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.

    Returns:
        A boolean reflecting whether to send a notification.
    """

    msg_prefix = f'Skipping notification on upcoming expiration for request {request.id} to user "{user.username}": '

    # If the allocation request does not have an expiration date, no need to notify
    if not request.expire:
        log.debug(msg_prefix + 'Request does not expire.')
        return False

    # If the request is already expired, it's too late to notify
    if request.expire <= date.today():
        log.debug(msg_prefix + 'Request has already expired.')
        return False

    # Check user notification preferences
    days_until_expire = request.get_days_until_expire()
    next_threshold = Preference.get_user_preference(user).get_expiration_threshold(days_until_expire)

    # If no notification threshold applies for the current number of days until expiration, do not notify
    if next_threshold is None:
        log.debug(msg_prefix + 'No notification threshold has been hit yet.')
        return False

    # Avoid spamming new users by skipping notifications for user accounts created
    # after the notification threshold
    if user.date_joined.date() >= date.today() - timedelta(days=next_threshold):
        log.debug(msg_prefix + 'User account created after notification threshold.')
        return False

    # Check if a notification was already sent at or below this threshold for this request
    if Notification.objects.filter(
        user=user,
        notification_type=Notification.NotificationType.request_expiring,
        metadata__request_id=request.id,
        metadata__days_to_expire__lte=next_threshold
    ).exists():
        log.debug(msg_prefix + 'Notification already sent for threshold.')
        return False

    # All checks passed — safe to notify
    return True


@shared_task()
def notify_upcoming_expirations() -> None:
    """Send a notification to all users with soon-to-expire allocations."""

    # Retrieve all approved allocation requests that expire in the future
    active_requests = AllocationRequest.objects.filter(
        status=AllocationRequest.StatusChoices.APPROVED,
        expire__gt=date.today()
    ).all()

    for request in active_requests:
        for user in request.team.get_all_members().filter(is_active=True):
            if should_notify_upcoming_expiration(user, request):
                notify_allocation_upcoming_expiration.delay(user, request, request.allocation_set)


def should_notify_past_expiration(user: User, request: AllocationRequest) -> bool:
    """Determine if a notification should be sent concerning the recent expiration of an allocation.

    Returns `True` if a notification is warranted by user preferences and
    an existing notification has not already been issued.

    Args:
        user: The user to notify.
        request: The allocation request to notify the user about.

    Returns:
        A boolean reflecting whether to send a notification.
    """

    # Check if a notification has already been sent
    if Notification.objects.filter(
        user=user,
        notification_type=Notification.NotificationType.request_expired,
        metadata__request_id=request.id,
    ).exists():
        log.debug(f'Skipping expiration notification for request {request.id} to user {user.username}: Notification already sent.')
        return False

    # Check user notification preferences
    return Preference.get_user_preference(user).notify_on_expiration


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
        for user in request.team.get_all_members().filter(is_active=True):
            if should_notify_past_expiration(user, request):
                notify_allocation_past_expiration.delay(user, request, request.allocation_set)
