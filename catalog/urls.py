from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CustomFieldDefinitionViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"custom-fields", CustomFieldDefinitionViewSet, basename="custom-field-definition")

urlpatterns = router.urls
