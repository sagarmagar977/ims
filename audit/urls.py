from rest_framework.routers import DefaultRouter

from .views import InventoryAuditLogViewSet

router = DefaultRouter()
router.register(r"audit-logs", InventoryAuditLogViewSet, basename="inventory-audit-log")

urlpatterns = router.urls
