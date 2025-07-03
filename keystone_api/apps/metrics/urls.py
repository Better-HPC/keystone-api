"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'metrics'

urlpatterns = [
    path('', MetricsView.as_view(), name='metrics'),
]
