# Chapter 30 — Deep Dive: `inventory/views.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 30
- Before this: Chapter 29
- After this: Chapter 31

## Learning Objectives
- Understand inventory API endpoint behavior and side effects.
- `inventory/views.py`
- `InventoryItemViewSet`, `FixedAssetViewSet`, `ConsumableStockViewSet`, `ConsumableStockTransactionViewSet`.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 30 — Deep Dive: `inventory/views.py`

## Learning Goals
- Understand inventory API endpoint behavior and side effects.

## Reference File
- `inventory/views.py`

## Deep Dive Walkthrough

## 1) Viewsets
- `InventoryItemViewSet`, `FixedAssetViewSet`, `ConsumableStockViewSet`, `ConsumableStockTransactionViewSet`.
- All use `IMSAccessPermission` and office-scoped querysets via `scope_queryset_by_user`.

## 2) Inventory create/update hooks
- `perform_create`: writes `CREATE` audit log with `item_snapshot`.
- `perform_update`: captures pre-update snapshot and writes `UPDATE` audit log.

## 3) Bulk import endpoint
- `@action(detail=False, methods=["post"], url_path="bulk-import")`.
- Reads CSV rows, validates each row with serializer, creates item on valid row.
- Writes audit entry for each successful import row.
- Returns `created`, `failed`, and row-level `errors`.

## 4) Stock transaction hook
- `perform_create` sets `performed_by` and writes audit event.
- For low-stock condition (`quantity <= min_threshold` with alerts enabled), sends email to configured recipients.

## Chapter 30 Outcome
You now understand where inventory APIs perform business side effects beyond plain CRUD: audit logging, CSV ingestion, and low-stock alerting.
```

## Topic 2 — Actual Implementation (Exact Repo Code)
Not present in current project.

## Rebuild Step (Hands-on Roadmap)
- Implement or review the files listed in this chapter only.
- Validate behavior discussed in the original chapter explanation.
- Confirm readiness for the next chapter transition.

## Chapter Summary
This chapter ties repository explanation to exact code references and prepares the next build step.

## Files Used
- Not present in current project.

