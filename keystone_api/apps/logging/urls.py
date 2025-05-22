"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'logging'

router = DefaultRouter()
router.register('apps', AppLogViewSet)
router.register('requests', RequestLogViewSet)
router.register('tasks', TaskResultViewSet)
router.register('audit', AuditLogViewSet)

urlpatterns = router.urls + [
    path('allocation-request/status-choices/', AuditLogActionChoicesView.as_view()),
]
