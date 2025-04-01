from django.views import View
from rest_framework.request import Request

from apps.users.models import Team


class ObjectRbacMixin:

    READ_METHODS = ('GET', 'HEAD', 'OPTIONS')
    WRITE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')
    ALL_METHODS = READ_METHODS + WRITE_METHODS

    def has_object_permission(self, request: Request, view: View, obj: Team) -> bool:
        """Return whether the request has permission to access a specific record."""

        role = obj.get_user_role(request.user)
        allowed_methods = self.RBAC.get(role, [])
        return request.method in allowed_methods
