"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'stats'

router = DefaultRouter()
router.register('grants', GrantStatsViewSet)
router.register('publications', PublicationStatsViewSet)

urlpatterns = router.urls
