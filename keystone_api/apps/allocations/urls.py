"""URL routing for the parent application."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *
from .views import CommentViewSet

app_name = 'allocations'

router = DefaultRouter()
router.register(r'allocations', AllocationViewSet)
router.register(r'attachments', AttachmentViewSet)
router.register(r'clusters', ClusterViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'requests', AllocationRequestViewSet)
router.register(r'reviews', AllocationReviewViewSet)

urlpatterns = router.urls
urlpatterns += [
    path('allocation-request/status-choices/', AllocationRequestStatusChoicesView.as_view()),
    path('allocation-review/status-choices/', AllocationReviewStatusChoicesView.as_view()),
]
