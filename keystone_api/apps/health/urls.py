"""URL routing for the parent application."""

from django.urls import re_path

from .views import *

app_name = 'health'

urlpatterns = [
    re_path(r'^(?:(?P<format>\w+)/)?$', HealthCheckView.as_view()),
]
