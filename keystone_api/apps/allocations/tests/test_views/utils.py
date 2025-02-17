from django.test import RequestFactory

from apps.allocations.views import AttachmentViewSet
from apps.users.models import User


def create_viewset_request(viewset, user: User) -> AttachmentViewSet:
    """Create a new viewset instance with a request from the given user"""

    request = RequestFactory()
    request.user = user

    viewset = viewset()
    viewset.request = request

    return viewset
