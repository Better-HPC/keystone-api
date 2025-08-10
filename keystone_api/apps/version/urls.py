"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'version'

urlpatterns = [
    path('', VersionView.as_view(), name='version'),
]
