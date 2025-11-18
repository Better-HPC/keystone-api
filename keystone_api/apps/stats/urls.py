"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'stats'

router = DefaultRouter()
router.register('grants', GrantStatsViewSet, basename='grants')
router.register('publications', PublicationStatsViewSet, basename='publications')
router.register('requests', AllocationRequestStatsViewSet, basename='requests')

urlpatterns = router.urls
