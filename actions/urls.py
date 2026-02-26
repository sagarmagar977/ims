from rest_framework.routers import DefaultRouter

from .views import ItemAssignmentViewSet

router = DefaultRouter()
router.register(r"item-assignments", ItemAssignmentViewSet, basename="item-assignment")

urlpatterns = router.urls
