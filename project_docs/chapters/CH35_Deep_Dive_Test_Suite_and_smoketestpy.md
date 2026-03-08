# Chapter 35 — Deep Dive: Test Suite and `.smoke_test.py`

## Learning Goals
- Understand what behaviors are currently covered by automated tests.
- Identify coverage gaps visible from existing test files.

## Reference Files
- `common/tests.py`
- `users/tests.py`
- `hierarchy/tests.py`
- `catalog/tests.py`
- `inventory/tests.py`
- `actions/tests.py`
- `audit/tests.py`
- `reports/tests.py`
- `.smoke_test.py`

## Test Coverage Map
- `common/tests.py`: deprecation headers for `/api/*` vs `/api/v1/*`.
- `users/tests.py`: self-privilege escalation prevention.
- `hierarchy/tests.py`: office write matrix by role.
- `catalog/tests.py`: category write matrix by role.
- `inventory/tests.py`: office scoping, role write restrictions, stock balance mutation, audit-on-bulk-import.
- `actions/tests.py`: assignment role matrix and audit-on-bulk-import.
- `audit/tests.py`: audit logs are read-only via API.
- `reports/tests.py`: export endpoint correctness (Excel/PDF signatures) and v1 report endpoint.

## `.smoke_test.py` role
- Procedural API sanity script that:
  - ensures admin/token,
  - exercises dashboard/report endpoints,
  - creates sample inventory/assignment/stock transaction,
  - checks summary/audit endpoints.

## Observed Gaps (from repository tests)
- No dedicated tests for settings env parsing branches.
- No dedicated tests for all report filters/fiscal-year edge cases.
- No dedicated tests for command modules.

## Chapter 35 Outcome
You now have a precise view of current automated verification coverage and the remaining untested paths.
