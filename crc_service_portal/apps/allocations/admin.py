from django.contrib import admin

from .models import *


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    """Admin interface for the `Cluster` model"""

    @staticmethod
    @admin.action
    def enable_selected_clusters(modeladmin, request, queryset) -> None:
        """Mark selected clusters as enabled"""

        queryset.update(enabled=True)

    @staticmethod
    @admin.action
    def disable_selected_clusters(modeladmin, request, queryset) -> None:
        """Mark selected clusters as disabled"""

        queryset.update(enabled=False)

    list_display = ['enabled', 'name', 'description']
    ordering = ['name']
    list_filter = ['enabled']
    search_fields = ['name', 'description']
    actions = [enable_selected_clusters, disable_selected_clusters]


class ProposalReviewInline(admin.StackedInline):
    """Inline admin interface for the `ProposalReview` model"""

    model = ProposalReview
    show_change_link = True
    readonly_fields = ('date_modified', )
    extra = 0


class AllocationInline(admin.TabularInline):
    """Inline admin interface for SU allocations"""

    model = Allocation
    show_change_link = True
    extra = 0


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin interface for the `Proposal` model"""

    list_display = ['user', 'title', 'submitted', 'approved']
    search_fields = ['user', 'title']
    ordering = ['submitted']
    list_filter = [
        ('submitted', admin.DateFieldListFilter),
        ('approved', admin.DateFieldListFilter),
    ]
    inlines = [AllocationInline, ProposalReviewInline]


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    """Admin interface for the `Allocation` model"""

    @staticmethod
    @admin.display
    def service_units(obj: Allocation) -> str:
        """Return an allocation's service units formatted as a human friendly string"""

        return f'{obj.sus:,}'

    @staticmethod
    @admin.display
    def proposal_approved(obj: Allocation) -> bool:
        """Return whether the allocation proposal has been marked as approved"""

        return obj.proposal.approved is not None

    list_display = ['user', 'cluster', 'expire', 'start', service_units, proposal_approved]
    ordering = ['user', 'cluster', '-expire']
    search_fields = ['user', 'cluster']
    list_filter = [
        ('start', admin.DateFieldListFilter),
        ('expire', admin.DateFieldListFilter),
    ]


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Admin interface for the `Publication` class"""

    @staticmethod
    @admin.display
    def title(obj: Publication) -> str:
        """Return an allocation's service units formatted as a human friendly string"""

        return obj.get_truncated_title(100)

    list_display = ['user', title, 'date']
    search_fields = ['user', 'title']
    list_filter = [
        ('date', admin.DateFieldListFilter),
    ]
