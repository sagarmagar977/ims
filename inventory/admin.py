from django.contrib import admin


from .models import ConsumableStock, ConsumableStockTransaction, FixedAsset, InventoryItem


admin.site.register(InventoryItem)
admin.site.register(FixedAsset)
admin.site.register(ConsumableStock)
admin.site.register(ConsumableStockTransaction)

    
# Register your models here.
