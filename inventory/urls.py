from rest_framework.routers import DefaultRouter

from .views import ConsumableStockTransactionViewSet, ConsumableStockViewSet, FixedAssetViewSet, InventoryItemViewSet

router = DefaultRouter()
router.register(r"inventory-items", InventoryItemViewSet, basename="inventory-item")
router.register(r"fixed-assets", FixedAssetViewSet, basename="fixed-asset")
router.register(r"consumable-stocks", ConsumableStockViewSet, basename="consumable-stock")
router.register(r"consumable-stock-transactions", ConsumableStockTransactionViewSet, basename="consumable-stock-transaction")

urlpatterns = router.urls
