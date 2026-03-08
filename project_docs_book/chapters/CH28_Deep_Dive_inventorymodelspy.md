# Chapter 28 — Deep Dive: `inventory/models.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 28
- Before this: Chapter 27
- After this: Chapter 29

## Learning Objectives
- Understand core inventory domain entities and constraints.
- `inventory/models.py`
- `InventoryStatus`: `ACTIVE`, `INACTIVE`, `DISPOSED`, `ASSIGNED`, `UNASSIGNED`.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 28 — Deep Dive: `inventory/models.py`

## Learning Goals
- Understand core inventory domain entities and constraints.

## Reference File
- `inventory/models.py`

## Deep Dive Walkthrough

## 1) Core enums
- `InventoryStatus`: `ACTIVE`, `INACTIVE`, `DISPOSED`, `ASSIGNED`, `UNASSIGNED`.
- `InventoryItemType`: `FIXED_ASSET`, `CONSUMABLE`.
- `StockTransactionType`: `STOCK_IN`, `STOCK_OUT`, `DAMAGE`, `ADJUSTMENT`.

## 2) `InventoryItem`
- Central entity linked to `Category` and `Office`.
- Includes item identity, financial fields, optional documents/media, and `dynamic_data` JSON.
- Indexes on `(category, office)`, `status`, `item_number`.
- `clean()` guards against incompatible subtype combinations and category/type mismatches.

## 3) Subtype tables
- `FixedAsset` (one-to-one with `InventoryItem`) for serial/warranty/invoice fields.
- `ConsumableStock` (one-to-one with `InventoryItem`) for quantity/threshold/alert settings.

## 4) Transaction table
- `ConsumableStockTransaction` records stock movement events with actor links and resulting balance.
- Indexes on `(stock, created_at)` and `transaction_type`.

## Chapter 28 Outcome
You now have a complete mental model of inventory schema design, subtype separation, and stock event persistence.
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

