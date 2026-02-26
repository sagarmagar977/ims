from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from catalog.models import Category
from hierarchy.models import Office, OfficeLevels
from inventory.models import InventoryItem

User = get_user_model()
admin, created = User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com'})
if created:
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password('admin123')
    admin.save()
else:
    admin.set_password('admin123')
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()

office, _ = Office.objects.get_or_create(name='Central Office', defaults={'level': OfficeLevels.CENTRAL, 'location_code': 'CENTRAL-001'})
if office.level != OfficeLevels.CENTRAL:
    office.level = OfficeLevels.CENTRAL
    office.location_code = office.location_code or 'CENTRAL-001'
    office.save()

laptop_cat, _ = Category.objects.get_or_create(name='Laptop', defaults={'is_consumable': False})
toner_cat, _ = Category.objects.get_or_create(name='Toner', defaults={'is_consumable': True})

client = APIClient()
resp = client.post('/api/auth/token/', {'username':'admin','password':'admin123'}, format='json')
print('token status', resp.status_code)
assert resp.status_code == 200, resp.content
access = resp.data['access']
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

print('dashboard status', client.get('/api/reports/dashboard-summary/').status_code)
print('recent activities status', client.get('/api/reports/recent-inventory-activities/').status_code)

item_payload = {
    'title': 'Laptop - Dell 5420',
    'item_number': 'ITM-0001',
    'item_type': 'FIXED_ASSET',
    'status': 'ACTIVE',
    'category': laptop_cat.id,
    'office': office.id,
    'amount': '1',
    'price': '1200.00',
    'currency': 'NPR'
}
item_resp = client.post('/api/inventory-items/', item_payload, format='json')
print('create item status', item_resp.status_code)
if item_resp.status_code not in (200, 201):
    print(item_resp.data)

item = InventoryItem.objects.filter(item_number='ITM-0001').first()
if item:
    assign_resp = client.post('/api/item-assignments/', {
        'item': item.id,
        'assigned_to_user': admin.id,
        'handover_date': '2026-02-25',
        'assign_till': '2026-03-25',
        'status': 'ASSIGNED'
    }, format='json')
    print('create assignment status', assign_resp.status_code)
    if assign_resp.status_code not in (200, 201):
        print(assign_resp.data)

cons_payload = {
    'title': 'Toner Cartridge',
    'item_number': 'CON-0001',
    'item_type': 'CONSUMABLE',
    'status': 'ACTIVE',
    'category': toner_cat.id,
    'office': office.id,
    'amount': '1'
}
cons_resp = client.post('/api/inventory-items/', cons_payload, format='json')
print('create consumable item status', cons_resp.status_code)
if cons_resp.status_code not in (200, 201):
    print(cons_resp.data)

cons_item = InventoryItem.objects.filter(item_number='CON-0001').first()
if cons_item:
    stock_resp = client.post('/api/consumable-stocks/', {
        'item': cons_item.id,
        'initial_quantity': '100',
        'quantity': '100',
        'min_threshold': '20',
        'unit': 'pcs'
    }, format='json')
    print('create stock status', stock_resp.status_code)
    if stock_resp.status_code not in (200, 201):
        print(stock_resp.data)
    if stock_resp.status_code in (200, 201):
        tx_resp = client.post('/api/consumable-stock-transactions/', {
            'stock': stock_resp.data['id'],
            'transaction_type': 'STOCK_OUT',
            'quantity': '5',
            'status': 'ON_BOARDED',
            'amount': '5',
            'department': 'Stores',
            'description': 'Issue to office'
        }, format='json')
        print('create stock tx status', tx_resp.status_code)
        if tx_resp.status_code not in (200, 201):
            print(tx_resp.data)

print('assignee summary status', client.get('/api/item-assignments/summary-by-assignee/').status_code)
print('audit logs status', client.get('/api/audit-logs/').status_code)
print('stock transactions list status', client.get('/api/consumable-stock-transactions/').status_code)
