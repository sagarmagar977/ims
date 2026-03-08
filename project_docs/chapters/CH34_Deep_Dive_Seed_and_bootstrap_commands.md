# Chapter 34 — Deep Dive: Seed and bootstrap commands

## Learning Goals
- Understand command-driven environment bootstrap and sample data seeding.

## Reference Files
- `common/management/commands/bootstrap_admin.py`
- `common/management/commands/seed_prd_data.py`
- `catalog/management/commands/seed_initial_categories.py`

## Deep Dive Walkthrough

## 1) `bootstrap_admin.py`
- Reads bootstrap credentials/profile from env vars.
- Skips safely when required env vars are absent.
- Upserts admin user with staff/superuser flags and password sync.

## 2) `seed_initial_categories.py`
- Seeds fixed-asset and consumable category lists idempotently.
- Supports `--dry-run` rollback mode.
- Reports created/updated/unchanged counts.

## 3) `seed_prd_data.py`
- Orchestrates idempotent seeding across modules:
  - offices, users, custom fields, inventory, assignments, stock transactions, audit logs.
- Calls `seed_initial_categories` first.
- Supports `--dry-run` transaction rollback.
- Uses concrete constant payload lists (`OFFICES`, `USERS`, `CUSTOM_FIELDS`, `ITEMS`).

## Chapter 34 Outcome
You now understand the project’s reproducible bootstrap/seed workflow and how it supports both local setup and PRD-aligned demo data.
