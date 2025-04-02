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

urlpatterns = router.urls + [
    path('allocation-request/status-choices/', AllocationRequestStatusChoicesView.as_view()),
    path('allocation-review/status-choices/', AllocationReviewStatusChoicesView.as_view()),
]
