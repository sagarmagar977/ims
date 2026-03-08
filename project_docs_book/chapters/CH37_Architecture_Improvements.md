# Chapter 37 — Architecture Improvements

## Build Roadmap Position
- Stage: Hardening
- You are here: Chapter 37
- Before this: Chapter 36
- After this: Chapter 38

## Learning Objectives
- Introduce a service layer for repeated business logic currently in viewsets.
- Standardize audit action selection logic into reusable domain helpers.
- Move CSV parsing/import flows into dedicated import services.

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
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

