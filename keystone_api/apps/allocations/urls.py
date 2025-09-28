"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'allocations'

router = DefaultRouter()
router.register('allocations', AllocationViewSet)
router.register('attachments', AttachmentViewSet)
router.register('clusters', ClusterViewSet)
router.register('comments', CommentViewSet)
router.register('requests', AllocationRequestViewSet)
router.register('reviews', AllocationReviewViewSet)
router.register('jobs', JobStatsViewSet)

urlpatterns = router.urls + [
    path('request-choices/status/', AllocationRequestStatusChoicesView.as_view()),
    path('review-choices/status/', AllocationReviewStatusChoicesView.as_view()),
]
