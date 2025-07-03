"""Top level URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path('', lambda *args: HttpResponse(f"Keystone API Version {settings.VERSION}"), name='home'),
    path('admin/', admin.site.urls),
    path('allocations/', include('apps.allocations.urls', namespace='alloc')),
    path('authentication/', include('apps.authentication.urls', namespace='authentication')),
    path('health/', include('apps.health.urls', namespace='health')),
    path('logs/', include('apps.logging.urls', namespace='logs')),
    path("metrics/", include('apps.metrics.urls', namespace='metrics')),
    path("notifications/", include('apps.notifications.urls', namespace="notifications")),
    path('openapi/', include('apps.openapi.urls', namespace='openapi')),
    path('research/', include('apps.research_products.urls', namespace='research')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('version/', include('apps.version.urls', namespace='version')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
