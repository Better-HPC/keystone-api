"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health')
]
