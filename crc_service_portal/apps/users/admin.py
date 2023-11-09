"""Extends the builtin Django admin interface for the parent application.

Extends and customizes the site-wide administration utility with
interfaces for managing application database constructs.
"""

import django.contrib.auth.admin
import django.contrib.auth.models
from django.conf import settings
from django.contrib import admin, auth

from .models import *

settings.JAZZMIN_SETTINGS['icons'].update({
    'users.User': 'fa fa-user',
    'users.Group': 'fa fa-user-shield',
    'users.Delegate': 'fa fa-users',
})

settings.JAZZMIN_SETTINGS['order_with_respect_to'].extend([
    'users.User', 'users.Group', 'users.Delegate'
])

# Remove the original authentication admin
admin.site.unregister(auth.models.User)
admin.site.unregister(auth.models.Group)


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    """Admin interface for managing user accounts"""


@admin.register(Group)
class GroupAdmin(auth.admin.GroupAdmin):
    """Admin interface for managing user groups"""


@admin.register(Delegate)
class ResearchGroupAdmin(admin.ModelAdmin):
    """Admin interface for managing research group delegates"""

    list_display = ['pi']
    filter_horizontal = ('delegates',)
