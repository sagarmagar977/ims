# Chapter 33 — Deep Dive: `reports/views.py`

## Learning Goals
- Understand report aggregation logic and export path reuse.

## Reference File
- `reports/views.py`

## Deep Dive Walkthrough

## 1) Dashboard aggregation
- Combines scoped counts from inventory, assignments, stocks, fixed assets, and offices.
- Derives assigned/unassigned counts using assignment distinct item logic.

## 2) Low-stock report
- Filters consumable stock by alert flag and threshold condition.
- Returns compact list payload for alert/report screens.

## 3) Assignment summary by office
- Uses grouped annotations with filtered counts for active/returned status.

## 4) Recent activities
- Pulls latest 50 scoped audit logs with item/actor display mapping.

## 5) Inventory report + exports
- `InventoryReportView.get_queryset` applies filters and fiscal-year window logic.
- `serialize_items` is reused by base JSON endpoint.
- CSV/Excel/PDF views all reuse the same filtered queryset from base class.

## Chapter 33 Outcome
You now understand how report endpoints share one filtering core while producing multiple output formats.
