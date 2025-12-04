"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'users'

router = DefaultRouter()
router.register('memberships', MembershipViewSet, 'membership')
router.register('teams', TeamViewSet, 'team')
router.register('users', UserViewSet, 'user')

urlpatterns = router.urls + [
    path('membership-choices/role/', MembershipRoleChoicesView.as_view(), name='membership-roles'),
]
