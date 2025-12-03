"""Extends the builtin Django admin interface for the parent application.

Extends and customizes the site-wide administration utility with
interfaces for managing application database constructs.
"""

from typing import Literal

from django.conf import settings
from django.contrib import admin

from .models import *

settings.JAZZMIN_SETTINGS['icons'].update({
    'notifications.Notification': 'fa fa-envelope',
    'notifications.Preference': 'fas fa-mail-bulk',
})

settings.JAZZMIN_SETTINGS['order_with_respect_to'].extend([
    'notifications.Preference',
    'notifications.Notification',
])


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for user notifications."""

    list_display = ('user', 'notification_type', 'subject', 'time', 'read')
    list_filter = ('read', 'notification_type', 'time')
    search_fields = ('user__username', 'subject', 'message')

    def has_change_permission(self, request, obj=None) -> Literal[False]:
        """Disable permissions for modifying records."""

        return False

    def has_add_permission(self, request, obj=None) -> Literal[False]:
        """Disable permissions for creating new records."""

        return False


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    """Admin interface for user notification preferences."""

    list_display = ('user',)
    search_fields = ('user__username',)
