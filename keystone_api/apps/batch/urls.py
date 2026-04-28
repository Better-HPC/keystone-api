"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'batch'

urlpatterns = [
    path('', JobApiView.as_view(), name='batch'),
]
