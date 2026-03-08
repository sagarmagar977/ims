# Chapter 38 — Refactoring

## High-Value Refactor Candidates
- Normalize repeated scoped-queryset patterns into shared mixins/helpers for viewsets.
- Extract CSV import loop templates from `inventory/views.py` and `actions/views.py`.
- Reduce repeated audit payload assembly in write hooks.
- Centralize enum literal usage (avoid direct string literals where enums exist).
- Add serializers/utilities for repeated display mapping (`performed_by_name`, assignment labels).

## Safety Strategy
1. Add/extend tests around target behavior first.
2. Refactor one module at a time.
3. Keep endpoint contracts and response schemas unchanged.
4. Re-run full test suite after each refactor chunk.

## Chapter 38 Outcome
You now have a safe, test-first refactoring plan mapped directly to duplication and complexity visible in this codebase.
