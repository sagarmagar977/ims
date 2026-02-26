from audit.models import InventoryActionType, InventoryAuditLog


def create_inventory_audit_log(*, item, action_type, user=None, before_data=None, after_data=None, remarks=""):
    InventoryAuditLog.objects.create(
        item=item,
        action_type=action_type,
        performed_by=user,
        before_data=before_data or {},
        after_data=after_data or {},
        remarks=remarks or "",
    )


def item_snapshot(item):
    return {
        "id": item.id,
        "title": item.title,
        "item_number": item.item_number,
        "status": item.status,
        "item_type": item.item_type,
        "amount": str(item.amount),
        "office_id": item.office_id,
        "category_id": item.category_id,
    }
