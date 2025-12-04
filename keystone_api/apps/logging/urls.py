"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'logging'

router = DefaultRouter()
router.register('audit', AuditLogViewSet, basename='audit')
router.register('requests', RequestLogViewSet, basename='request')
router.register('tasks', TaskResultViewSet, basename='task')

urlpatterns = router.urls
