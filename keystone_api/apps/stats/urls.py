"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = "stats"

urlpatterns = [
    path("grants/", GrantStatsView.as_view(), name="grant-stats"),
    path("notifications/", NotificationStatsView.as_view(), name="notification-stats"),
    path("publications/", PublicationStatsView.as_view(), name="publication-stats"),
    path("requests/", AllocationRequestStatsView.as_view(), name="request-stats"),
]
