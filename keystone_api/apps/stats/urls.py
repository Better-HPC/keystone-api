"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'stats'

urlpatterns = [
    path('grants/', GrantStatsView.as_view(), name='grant-detail'),
    path('publications/', PublicationStatsView.as_view(), name='publication-detail'),
    path('notifications/', PublicationStatsView.as_view(), name='publication-detail'),
    path('requests/', AllocationRequestStatsView.as_view(), name='request-detail'),
]
