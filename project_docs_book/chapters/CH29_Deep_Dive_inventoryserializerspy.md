# Chapter 29 — Deep Dive: `inventory/serializers.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 29
- Before this: Chapter 28
- After this: Chapter 30

## Learning Objectives
- Understand validation rules and stock mutation behavior in serializers.
- `inventory/serializers.py`
- Validates category/type compatibility.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 29 — Deep Dive: `inventory/serializers.py`

## Learning Goals
- Understand validation rules and stock mutation behavior in serializers.

## Reference File
- `inventory/serializers.py`

## Deep Dive Walkthrough

## 1) `InventoryItemSerializer`
- Validates category/type compatibility.
- Adds computed read fields:
  - `serial_number` from fixed-asset relation,
  - `assigned_to` and `assignment_status` from active assignment query.

## 2) `FixedAssetSerializer`
- Rejects fixed-asset subtype for consumable categories.
- Rejects dual subtype state when `consumable_stock` exists.

## 3) `ConsumableStockSerializer`
- Rejects consumable subtype for non-consumable categories.
- Rejects dual subtype state when `fixed_asset` exists.
- Adds computed `stock_status`:
  - `OUT_OF_STOCK`, `LOW_STOCK`, `ON_BOARDED`.

## 4) `ConsumableStockTransactionSerializer`
- `validate_quantity` enforces positive values.
- `create()` is transactional and:
  - decrements for `STOCK_OUT`/`DAMAGE`,
  - increments for other transaction types,
  - prevents insufficient stock,
  - writes `balance_after`,
  - persists updated stock quantity.
- Adds display read fields for item and performer names.

## Chapter 29 Outcome
You can now trace serializer-level protection and mutation logic that keeps inventory and stock balances consistent.
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

