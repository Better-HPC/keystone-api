"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'cluster'

router = DefaultRouter()
router.register('jobs', JobStatsViewSet)

urlpatterns = router.urls
