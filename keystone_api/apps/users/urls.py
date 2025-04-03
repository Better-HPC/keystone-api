"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'users'

router = DefaultRouter()
router.register('membership', MembershipViewSet)
router.register('teams', TeamViewSet)
router.register('users', UserViewSet)

urlpatterns = router.urls + [
    path('team-membership/role-choices/', MembershipRoleChoicesView.as_view(), name='team_membership_roles'),
]
