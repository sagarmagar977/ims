# Chapter 33 — Deep Dive: `reports/views.py`

## Build Roadmap Position
- Stage: Deep Dive
- You are here: Chapter 33
- Before this: Chapter 32
- After this: Chapter 34

## Learning Objectives
- Understand report aggregation logic and export path reuse.
- `reports/views.py`
- Combines scoped counts from inventory, assignments, stocks, fixed assets, and offices.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
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

