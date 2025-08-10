"""URL routing for the parent application."""

from rest_framework.routers import DefaultRouter

from .views import *

app_name = 'research_products'

router = DefaultRouter()
router.register('grants', GrantViewSet)
router.register('publications', PublicationViewSet)

urlpatterns = router.urls
