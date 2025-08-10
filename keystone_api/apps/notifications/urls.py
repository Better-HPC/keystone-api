"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'notifications'

router = DefaultRouter()
router.register('notifications', NotificationViewSet)
router.register('preferences', PreferenceViewSet)

urlpatterns = router.urls + [
    path('allocation-request/status-choices/', NotificationTypeChoicesView.as_view()),
]
