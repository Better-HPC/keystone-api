from datetime import date, timedelta

from celery import shared_task

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
        expire__gt=date.today() - timedelta(days=3),
    ).select_related(
        "team"
    ).prefetch_related(
        "allocation_set",
        "team__users",
    )

    for request in expired_requests:
        allocations = request.allocation_set.all()
        team_members = request.team.users.filter(is_active=True)

        for user in team_members:
            user_preferences = Preference.get_user_preference(user)
            should_notify = should_notify_past_expiration(user_preferences, request)

            if should_notify:
                send_past_expiration_notice.delay(
                    user_name=user.username,
                    user_first=user.first_name,
                    user_last=user.last_name,
                    req_id=request.id,
                    req_title=request.title,
                    req_team=request.team.name,
                    req_submitted=request.submitted,
                    req_active=request.active,
                    req_expire=request.expire,
                    allocations=tuple(
                        {
                            'alloc_cluster': alloc.cluster.name,
                            'alloc_requested': alloc.requested or 0,
                            'alloc_awarded': alloc.awarded or 0,
                            'alloc_final': alloc.final or 0,
                        } for alloc in allocations
                    )
                )


@shared_task()
def send_past_expiration_notice(
    user_name: str,
    user_first: str,
    user_last: str,
    req_id: int,
    req_title: str,
    req_team: str,
    req_submitted: date,
    req_active: date | None = None,
    req_expire: date | None = None,
    allocations: tuple[dict] = tuple(),
) -> None:
    """Send a notification to alert a user their allocation request has expired.

    When persisting the notification record to the database, the allocation request
    ID is saved as notification metadata.

    Args:
        user_name: The username of the user.
        user_first: The first name of the user.
        user_last: The last name of the user.
        req_id: The ID of the allocation request.
        req_title: The title of the allocation request.
        req_team: The name of the team the allocation request belongs to.
        req_submitted: The date the allocation request was submitted.
        req_active: The date the allocation request became active.
        req_expire: The date the allocation request expires.
        allocations: A list of allocations tied to the allocation request.
    """

    user = User.objects.get(username=user_name)
    metadata = {'request_id': req_id}

    context = {
        'user_name': user_name,
        'user_first': user_first,
        'user_last': user_last,
        'req_id': req_id,
        'req_title': req_title,
        'req_team': req_team,
        'req_submitted': req_submitted,
        'req_active': req_active,
        'req_expire': req_expire,
        'allocations': allocations
    }

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{req_id} has expired',
        template='past_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expired,
        notification_metadata=metadata,
    )
