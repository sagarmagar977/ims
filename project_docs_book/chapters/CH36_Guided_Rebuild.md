# Chapter 36 — Guided Rebuild

## Build Roadmap Position
- Stage: Hardening
- You are here: Chapter 36
- Before this: Chapter 35
- After this: Chapter 37

## Learning Objectives
- JWT auth and authenticated-by-default API behavior.
- Dual routing under `/api/` and `/api/v1/`.
- Office-scoped querysets on domain endpoints.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 36 — Guided Rebuild

## Goal
Rebuild the reference backend in learning order using only existing project patterns.

## Rebuild Sequence
1. Initialize Django project and custom user model (`users.User`).
2. Add hierarchy module (`Office`) and office tree relations.
3. Add catalog module (`Category`, `CustomFieldDefinition`).
4. Add inventory core (`InventoryItem`, `FixedAsset`, `ConsumableStock`).
5. Add actions workflow (`ItemAssignment` constraints + endpoints).
6. Add audit module and helper utility (`create_inventory_audit_log`).
7. Add reports endpoints and export classes.
8. Add shared controls (`IMSAccessPermission`, office scoping helpers, legacy middleware).
9. Add seeding/bootstrap commands.
10. Add test suite and smoke script.

## Required Runtime Contracts
- JWT auth and authenticated-by-default API behavior.
- Dual routing under `/api/` and `/api/v1/`.
- Office-scoped querysets on domain endpoints.
- Audit logs for inventory and assignment write operations.

## Verification Checklist
- Run migrations.
- Seed categories and PRD data.
- Obtain token and call dashboard endpoint.
- Validate role matrix using existing tests.

## Chapter 36 Outcome
You now have a concrete rebuild order that mirrors the actual repository architecture and dependencies.
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

