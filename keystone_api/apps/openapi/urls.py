"""URL routing for the parent application."""

from django.urls import path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularYAMLAPIView

app_name = 'openapi'

urlpatterns = [
    path('json', SpectacularJSONAPIView.as_view(), name='json'),
    path('yaml', SpectacularYAMLAPIView.as_view(), name='yaml')
]
