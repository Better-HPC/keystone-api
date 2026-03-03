from datetime import date, timedelta

from celery import shared_task
from django.db.models import Prefetch, Q

from apps.allocations.models import AllocationRequest
from apps.users.models import User
from ..models import Notification, Preference
from ..shortcuts import send_notification_template

__all__ = [
    'notify_upcoming_expirations',
    'send_upcoming_expiration_notice',
]


def should_notify_upcoming_expiration(user: User, request: AllocationRequest) -> bool:
    """Determine whether a user should be notified about an upcoming request expiration.

    Args:
        user: The user to check notification preferences for.
        request: The allocation request that will expire soon.

    Returns:
        A boolean indicating whether to send a notification.
    """

    # Do not notify if request does not expire
    if not request.expire:
        return False

    # Do not notify if request is already expired
    if request.expire <= date.today():
        return False

    preference = Preference.get_user_preference(user)

    # Do not notify if there is no expiration threshold in user preferences
    days_until_expire = (request.expire - date.today()).days
    next_threshold = preference.get_expiration_threshold(days_until_expire)
    if next_threshold is None:
        return False

    # Do not notify if the user joined after the notification threshold
    user_join_date = preference.user.date_joined.date()
    if user_join_date >= date.today() - timedelta(days=next_threshold):
        return False

    # Do not notify if the allocation request went active after the notification threshold
    if request.active >= date.today() - timedelta(days=next_threshold):
        return False

    # Do not notify if the user has already been notified for this threshold
    if Notification.objects.filter(
        user=preference.user,
        metadata__request_id=request.id,
        metadata__days_to_expire__lte=next_threshold,
        notification_type=Notification.NotificationType.request_expiring,
    ).exists():
        return False

    return True


@shared_task()
def notify_upcoming_expirations() -> None:
    """Send a notification to all users with soon-to-expire allocations."""

    # Retrieve all approved allocation requests that expire in the future
    active_requests = AllocationRequest.objects.filter(
        status=AllocationRequest.StatusChoices.APPROVED,
        expire__gt=date.today()
    ).select_related(
        "team"
    ).prefetch_related(
        # Prefetch active team members and assign to the `active_users` attribute
        Prefetch("team__users", queryset=User.objects.filter(is_active=True), to_attr="active_users")
    )

    for request in active_requests:
        for user in request.team.active_users:
            if should_notify_upcoming_expiration(user, request):
                send_upcoming_expiration_notice.delay(user.id, request.id)


@shared_task()
def send_upcoming_expiration_notice(user_id: int, req_id: int) -> None:
    """Notify a user their allocation request will expire soon.

    When persisting the notification record to the database, the allocation request
    ID and the days remaining until the expiration date are saved as notification metadata.

    Args:
        user_id: ID for the user to notify.
        req_id: ID for the allocation request to notify about.
    """

    user = User.objects.get(id=user_id)
    expiring_request = AllocationRequest.objects \
        .select_related("team") \
        .prefetch_related("allocation_set__cluster") \
        .only("id", "title", "team__name", "submitted", "active", "expire") \
        .get(id=req_id)

    # Check notification preferences and database state in case they changed
    # since the task was scheduled
    if not should_notify_upcoming_expiration(user, expiring_request):
        return

    upcoming_requests = AllocationRequest.objects \
        .filter(
            Q(status=AllocationRequest.StatusChoices.PENDING) |
            Q(status=AllocationRequest.StatusChoices.APPROVED, expire__gt=date.today()) |
            Q(status=AllocationRequest.StatusChoices.APPROVED, expire__isnull=True),
            team=expiring_request.team,
        ) \
        .only("id", "title", "submitted", "active", "expire", "status")

    # Metadata used to track the uniqueness of the notification
    days_until_expire = (expiring_request.expire - date.today()).days if expiring_request.expire else None
    metadata = {
        'request_id': req_id,
        'days_to_expire': days_until_expire
    }

    # Values injected into the HTML template
    context = {
        'user_name': user.username,
        'user_first': user.first_name,
        'user_last': user.last_name,
        'req_id': expiring_request.id,
        'req_title': expiring_request.title,
        'req_team': expiring_request.team.name,
        'req_submitted': expiring_request.submitted,
        'req_active': expiring_request.active,
        'req_expire': expiring_request.expire,
        'req_days_left': days_until_expire,
        'allocations': tuple(
            {
                'alloc_cluster': alloc.cluster.name,
                'alloc_requested': alloc.requested or 0,
                'alloc_awarded': alloc.awarded or 0,
            } for alloc in expiring_request.allocation_set.all()
        ),
        'upcoming_requests': tuple(
            {
                'id': req.id,
                'title': req.title,
                'submitted': req.submitted,
                'active': req.active,
                'expire': req.expire,
            } for req in upcoming_requests.all()
        ),
    }

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{req_id} is expiring soon',
        template='upcoming_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expiring,
        notification_metadata=metadata,
    )
