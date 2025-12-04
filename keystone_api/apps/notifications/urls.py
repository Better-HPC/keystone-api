"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'notifications'

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename="notification")
router.register('preferences', PreferenceViewSet, basename="preference")

urlpatterns = router.urls + [
    path('notification-choices/type', NotificationTypeChoicesView.as_view(), name='notification-type-choices'),
]
