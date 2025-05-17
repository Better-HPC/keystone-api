"""Extends the builtin Django admin interface for the parent application.

Extends and customizes the site-wide administration utility with
interfaces for managing application database constructs.
"""

import django.contrib.auth.admin
from django.conf import settings
from django.contrib import admin, auth
from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpRequest

from .models import *

settings.JAZZMIN_SETTINGS['icons'].update({
    'users.User': 'fa fa-user',
    'users.Team': 'fa fa-users',
})

settings.JAZZMIN_SETTINGS['order_with_respect_to'].extend([
    'users.User', 'users.Team'
])


@admin.register(User)
class UserAdmin(auth.admin.UserAdmin):
    """Admin interface for managing user accounts."""

    @admin.action
    def activate_selected_users(self, request, queryset) -> None:
        """Mark selected users as active."""

        queryset.update(is_active=True)

    @admin.action
    def deactivate_selected_users(self, request, queryset) -> None:
        """Mark selected users as inactive."""

        queryset.update(is_active=False)

    readonly_fields = ('last_login', 'date_joined', 'is_ldap_user')
    actions = [activate_selected_users, deactivate_selected_users]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'department', 'role']
    fieldsets = (
        ('User Info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'department',
                'role',
                'last_login',
                'date_joined',
                'is_ldap_user'
            )
        }),
        ('Credentials', {
            'fields': (
                'username',
                'password'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
        })
    )


class MembershipInline(admin.TabularInline):
    """Inline interface for managing team membership."""

    model = Membership
    raw_id_fields = ('user',)
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin interface for managing user teams."""

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Define the base database query used for fetching displayed records.

        Optimizes database interactions by prefetching related data.
        """

        # Define query for prefetching owner memberships
        owner_memberships = Membership.objects.filter(
            role=Membership.Role.OWNER
        ).select_related('user')

        return super().get_queryset(
            request
        ).prefetch_related(
            Prefetch('membership', queryset=owner_memberships, to_attr='_prefetched_owner_memberships'),
        ).annotate(
            member_count=Count('users')
        )

    @staticmethod
    @admin.display
    def owners(obj: Team) -> str:
        """Return a CSV of team owners."""

        owners = [membership.user.username for membership in obj._prefetched_owner_memberships]
        return ', '.join(owners)

    @staticmethod
    @admin.display(ordering='member_count')
    def total_members(obj: Team) -> int:
        """Return the total number of team members."""

        return obj.member_count

    list_display = ('name', 'is_active', 'total_members', 'owners')
    search_fields = ('name',)
    list_filter = ('is_active',)
    inlines = [MembershipInline]
