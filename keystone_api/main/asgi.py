"""Expose an ASGI callable as a module-level variable named `application`."""

from django.conf import settings
from django.core.asgi import get_asgi_application
from servestatic import ServeStaticASGI

application = ServeStaticASGI(get_asgi_application(), root=settings.STATIC_ROOT)
