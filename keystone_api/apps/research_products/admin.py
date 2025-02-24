"""Extends the builtin Django admin interface for the parent application.

Extends and customizes the site-wide administration utility with
interfaces for managing application database constructs.
"""

from django.conf import settings
from django.contrib import admin

from .models import *

settings.JAZZMIN_SETTINGS['icons'].update({
    'research_products.Grant': 'fa fa-piggy-bank',
    'research_products.Publication': 'fas fa-book-open',
})


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Admin interface for the `Publication` class."""

    @staticmethod
    @admin.display
    def title(obj: Publication) -> str:
        """Return a publication's title as a human/table friendly string."""

        # Rely on the object to determine the appropriate string title representation
        return str(obj)

    list_display = ['team', 'title', 'submitted', 'published', 'preparation']
    list_display_links = list_display
    search_fields = ['title', 'team__name']
    list_filter = [
        ('submitted', admin.DateFieldListFilter),
        ('published', admin.DateFieldListFilter),
        ('preparation', admin.BooleanFieldListFilter),
    ]


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    """Admin interface for the `Grant` class."""

    @staticmethod
    @admin.display
    def amount(obj: Grant) -> str:
        """Return the allocation's service units as a human friendly string."""

        return f'${int(obj.amount):,}'

    list_display = ['team', 'fiscal_year', amount, 'agency', 'start_date', 'end_date']
    list_display_links = list_display
    ordering = ['team', '-fiscal_year']
    search_fields = ['title', 'agency', 'fiscal_year', 'team__name']
    list_filter = [
        ('start_date', admin.DateFieldListFilter),
        ('end_date', admin.DateFieldListFilter),
    ]
