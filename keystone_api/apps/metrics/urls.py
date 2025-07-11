"""URL routing for the parent application."""

from django.urls import path
from django_prometheus import exports

app_name = 'metrics'

urlpatterns = [
    path("metrics", exports.ExportToDjangoView, name="prometheus-django-metrics")
]
