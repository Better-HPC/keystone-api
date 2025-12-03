"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'allocations'

router = DefaultRouter()
router.register('allocations', AllocationViewSet, basename='allocation')
router.register('attachments', AttachmentViewSet, basename='attachment')
router.register('clusters', ClusterViewSet, basename='cluster')
router.register('comments', CommentViewSet, basename='comment')
router.register('requests', AllocationRequestViewSet, basename='request')
router.register('reviews', AllocationReviewViewSet, basename='review')
router.register('jobs', JobStatsViewSet, basename='job')

urlpatterns = router.urls + [
    path('request-choices/status/', AllocationRequestStatusChoicesView.as_view(), name='request-status-choices'),
    path('review-choices/status/', AllocationReviewStatusChoicesView.as_view(), name='review-status-choices'),
]
