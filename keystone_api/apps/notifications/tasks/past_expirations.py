from datetime import date, timedelta

from celery import shared_task
from django.db.models import Prefetch

from apps.allocations.models import AllocationRequest
from apps.users.models import User
from ..models import Notification, Preference
from ..shortcuts import send_notification_template

__all__ = [
    'notify_past_expirations',
    'send_past_expiration_notice',
]


def should_notify_past_expiration(user: User, request: AllocationRequest) -> bool:
    """Determine whether a user should be notified about an expired allocation request.

    Args:
        user: The user to check notification preferences for.
        request: The expired allocation request.

    Returns:
        A boolean indicating whether to send a notification.
    """

    if Notification.objects.filter(
        user=user,
        metadata__request_id=request.id,
        notification_type=Notification.NotificationType.request_expired,
    ).exists():
        return False

    return Preference.get_user_preference(user).notify_on_expiration


@shared_task()
def notify_past_expirations() -> None:
    """Send a notification to all users with expired allocations."""

    # Retrieve all allocation requests that expired within the last three days
    expired_requests = AllocationRequest.objects.filter(
        status=AllocationRequest.StatusChoices.APPROVED,
        expire__lte=date.today(),
        expire__gt=date.today() - timedelta(days=3)
    ).select_related(
        "team"
    ).prefetch_related(
        # Prefetch active team members and assign to the `active_users` attribute
        Prefetch("team__users", queryset=User.objects.filter(is_active=True), to_attr="active_users")
    )

    for request in expired_requests:
        for user in request.team.active_users:
            if should_notify_past_expiration(user, request):
                send_past_expiration_notice.delay(user.id, request.id)


@shared_task()
def send_past_expiration_notice(user_id: int, req_id: int) -> None:
    """Notify a user their allocation request has expired.

    When persisting the notification record to the database, the allocation request
    ID is saved as notification metadata.

    Args:
        user_id: ID for the user to notify.
        req_id: ID for the allocation request to notify about.
    """

    user = User.objects.get(id=user_id)
    request = AllocationRequest.objects \
        .select_related("team") \
        .prefetch_related("allocation_set__cluster") \
        .only("id", "title", "team__name", "submitted", "active", "expire") \
        .get(id=req_id)

    metadata = {'request_id': req_id}
    context = {
        'user_name': user.username,
        'user_first': user.first_name,
        'user_last': user.last_name,
        'req_id': request.id,
        'req_title': request.title,
        'req_team': request.team.name,
        'req_submitted': request.submitted,
        'req_active': request.active,
        'req_expire': request.expire,
        'allocations': tuple(
            {
                'alloc_cluster': alloc.cluster.name,
                'alloc_requested': alloc.requested or 0,
                'alloc_awarded': alloc.awarded or 0,
                'alloc_final': alloc.final or 0,
            } for alloc in request.allocation_set.all()
        )
    }

    # Perform check in case user preferences or database state
    # changed since the task was scheduled
    if not should_notify_past_expiration(user, request):
        return

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{req_id} has expired',
        template='past_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expired,
        notification_metadata=metadata,
    )
