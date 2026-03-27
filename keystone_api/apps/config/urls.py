"""URL routing for the config application."""

from django.urls import path

from .views import *

app_name = 'config'

urlpatterns = [
    path('', ConfigView.as_view(), name='config'),
]
