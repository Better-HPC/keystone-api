"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'stats'

urlpatterns = [
    path('grants/', GrantStatsView.as_view(), name='grant-detail'),
    path('publications/', PublicationStatsView.as_view(), name='publication-detail'),
    path('notifications/', NotificationStatsView.as_view(), name='notifications-detail'),
    path('requests/', AllocationRequestStatsView.as_view(), name='request-detail'),
]
