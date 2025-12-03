"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'stats'

router = DefaultRouter()
router.register('grants', GrantStatsViewSet, basename='grant')
router.register('publications', PublicationStatsViewSet, basename='publication')
router.register('requests', AllocationRequestStatsViewSet, basename='request')

urlpatterns = router.urls
