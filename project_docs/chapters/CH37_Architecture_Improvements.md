# Chapter 37 — Architecture Improvements

## Improvement Targets (Based on Current Code)
- Introduce a service layer for repeated business logic currently in viewsets.
- Standardize audit action selection logic into reusable domain helpers.
- Move CSV parsing/import flows into dedicated import services.
- Add dedicated module(s) for async tasks if Celery/Redis are intended for use.
- Formalize report query builders to reduce logic duplication across report endpoints.

## Why These Improve Current Design
- Reduces viewset complexity.
- Lowers duplication across inventory/actions/report paths.
- Makes testing of business rules easier without API-layer coupling.

## Constraints from Reference Project
- These are proposed improvements; service/task modules are not present in current repository.

## Chapter 37 Outcome
You can now distinguish current implemented architecture from practical next-step architecture improvements grounded in observed code patterns.
