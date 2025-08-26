from datetime import date, timedelta

from celery import shared_task

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

    if not request.expire:
        return False

    if request.expire <= date.today():
        return False

    preference = Preference.get_user_preference(user)

    days_until_expire = (request.expire - date.today()).days
    next_threshold = preference.get_expiration_threshold(days_until_expire)
    if next_threshold is None:
        return False

    user_join_date = preference.user.date_joined.date()
    if user_join_date >= date.today() - timedelta(days=next_threshold):
        return False

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
        "allocation_set",
        "team__users",
    )

    for request in active_requests:
        allocations = request.allocation_set.all()
        team_members = request.team.users.filter(is_active=True)

        for user in team_members:
            user_preferences = Preference.get_user_preference(user)
            should_notify = should_notify_upcoming_expiration(user_preferences, request)

            if should_notify:
                send_upcoming_expiration_notice.delay(
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
                        } for alloc in allocations
                    )
                )


@shared_task()
def send_upcoming_expiration_notice(
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
    """Send a notification to alert a user their allocation request will expire soon.

    When persisting the notification record to the database, the allocation request
    ID and the days remaining until the expiration date are saved as notification metadata.

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
    days_until_expire = (req_expire - date.today()).days if req_expire else None

    metadata = {
        'request_id': req_id,
        'days_to_expire': days_until_expire
    }

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
        'req_days_left': days_until_expire,
        'allocations': allocations
    }

    send_notification_template(
        user=user,
        subject=f'Your HPC allocation #{req_id} is expiring soon',
        template='upcoming_expiration.html',
        context=context,
        notification_type=Notification.NotificationType.request_expiring,
        notification_metadata=metadata,
    )
