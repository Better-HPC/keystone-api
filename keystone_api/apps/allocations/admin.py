"""Extends the builtin Django admin interface for the parent application.

Extends and customizes the site-wide administration utility with
interfaces for managing application database constructs.
"""

from django.conf import settings
from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .models import *

settings.JAZZMIN_SETTINGS['icons'].update({
    'allocations.Cluster': 'fa fa-server',
    'allocations.Allocation': 'fas fa-coins',
    'allocations.AllocationRequest': 'fa fa-file-alt',
})

settings.JAZZMIN_SETTINGS['order_with_respect_to'].extend([
    'allocations.Cluster',
    'allocations.AllocationRequest',
    'allocations.Allocation'
])


class AllocationInline(admin.TabularInline):
    """Inline admin interface for the `Allocation` model."""

    model = Allocation
    show_change_link = True
    extra = 1


class AllocationReviewInline(admin.StackedInline):
    """Inline admin interface for the `AllocationReview` model."""

    model = AllocationReview
    verbose_name = 'Review'
    show_change_link = True
    readonly_fields = ('last_modified',)
    extra = 1


class AttachmentInline(admin.TabularInline):
    """Inline interface for the `Attachment` model."""

    model = Attachment
    show_change_link = True
    readonly_fields = ('name',)
    extra = 1


class CommentInline(admin.StackedInline):
    """Inline admin interface for the `Comment` model."""

    model = Comment
    verbose_name = 'Comment'
    show_change_link = True
    readonly_fields = ('created',)
    extra = 1


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    """Admin interface for the `Allocation` model."""

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Define the base database query used for fetching displayed records.

        Optimizes database interactions by prefetching related data.
        """

        qs = super().get_queryset(request)
        return qs.select_related('request__team', 'cluster', 'request')

    @staticmethod
    @admin.display(ordering='request__team__name')
    def team(obj: Allocation) -> str:
        """Return the name of the user team the allocation is assigned to."""

        return obj.request.team.name

    @staticmethod
    @admin.display(ordering='request__title')
    def request(obj: Allocation) -> str:
        """Return the title of the allocation's corresponding request."""

        return obj.request.title

    @staticmethod
    @admin.display(ordering='cluster__name')
    def cluster(obj: Allocation) -> str:
        """Return the name of the cluster the allocation is assigned to."""

        return obj.cluster.name

    @staticmethod
    @admin.display(ordering='request__status')
    def status(obj: Allocation) -> str:
        """Return the status of the corresponding allocation request."""

        return obj.request.StatusChoices(obj.request.status).label

    list_display = ['team', 'request', 'cluster', 'requested', 'awarded', 'final', 'status']
    list_display_links = list_display
    ordering = ['request__team__name', 'cluster']
    search_fields = ['request__team__name', 'request__title', 'cluster__name']
    list_filter = [
        ('request__status', admin.ChoicesFieldListFilter)
    ]


@admin.register(AllocationRequest)
class AllocationRequestAdmin(admin.ModelAdmin):
    """Admin interface for the `AllocationRequest` model."""

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Define the base database query used for fetching displayed records.

        Optimizes database interactions by prefetching related data.
        """

        qs = super().get_queryset(request)
        return qs.select_related('team').annotate(review_count=Count('allocationreview'))

    @staticmethod
    @admin.display(ordering='team__name')
    def team(obj: Allocation) -> str:
        """Return the name of the user team the allocation is assigned to."""

        return obj.team.name

    @staticmethod
    @admin.display(ordering='review_count')
    def reviews(obj: AllocationRequest) -> int:
        """Return the total number of submitted reviews."""

        return obj.review_count

    list_display = ['team', 'title', 'submitted', 'active', 'expire', 'reviews', 'status']
    list_display_links = list_display
    search_fields = ['title', 'description', 'team__name']
    ordering = ['submitted']
    list_filter = [
        ('submitted', admin.DateFieldListFilter),
        ('active', admin.DateFieldListFilter),
        ('expire', admin.DateFieldListFilter),
        ('status', admin.ChoicesFieldListFilter),
    ]
    inlines = [AllocationInline, AllocationReviewInline, AttachmentInline, CommentInline]


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    """Admin interface for the `Cluster` model."""

    @admin.action
    def enable_selected_clusters(self, request, queryset) -> None:
        """Mark selected clusters as enabled."""

        queryset.update(enabled=True)

    @admin.action
    def disable_selected_clusters(self, request, queryset) -> None:
        """Mark selected clusters as disabled."""

        queryset.update(enabled=False)

    list_display = ['enabled', 'name', 'description']
    list_display_links = list_display
    ordering = ['name']
    list_filter = ['enabled']
    search_fields = ['name', 'description']
    actions = [enable_selected_clusters, disable_selected_clusters]
