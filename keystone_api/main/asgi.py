"""Expose an ASGI callable as a module-level variable named `application`."""

import os

from django.conf import settings
from django.core.asgi import get_asgi_application
from servestatic import ServeStaticASGI

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keystone_api.main.settings')

application = ServeStaticASGI(get_asgi_application(), root=settings.STATIC_ROOT)
