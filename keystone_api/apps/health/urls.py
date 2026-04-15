"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'health'

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health'),
    path('json/', HealthCheckJsonView.as_view(), name='json'),
    path('prom/', HealthCheckPrometheusView.as_view(), name='prometheus'),
]
