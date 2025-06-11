"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'notifications'

router = DefaultRouter()
router.register('notifications', NotificationViewSet)
router.register('preferences', PreferenceViewSet)

urlpatterns = router.urls
