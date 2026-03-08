# Chapter 39 — Performance Review

## Build Roadmap Position
- Stage: Hardening
- You are here: Chapter 39
- Before this: Chapter 38
- After this: Course complete and review loop

## Learning Objectives
- Database indexes on key query/filter fields across inventory, actions, audit, hierarchy, and catalog.
- Common use of `select_related` in report and viewset querysets.
- Pagination enabled globally (`PAGE_SIZE = 25`).

## Topic 1 — Chapter Guide
### What this is
This chapter explains one part of the repository and anchors learning to real project files.
### Why this exists in this project
It is a required stepping stone in the zero-to-final repository understanding flow.
### How it works here (actual flow)
The original chapter explanation is preserved below and then connected directly to exact source code.

### Original Chapter Explanation
```markdown
# Chapter 39 — Performance Review

## Current Performance-Relevant Strengths
- Database indexes on key query/filter fields across inventory, actions, audit, hierarchy, and catalog.
- Common use of `select_related` in report and viewset querysets.
- Pagination enabled globally (`PAGE_SIZE = 25`).
- DRF throttle classes configured (`anon` and `user` rates).

## Current Performance Risks (Observed)
- Several report/list endpoints build Python lists from querysets, which can become heavy at high row counts.
- CSV import executes per-row serializer saves without batching.
- Email alert trigger is synchronous in stock transaction create path.
- Query complexity in summary/report endpoints may grow with larger data volumes.

## Practical Next Steps
1. Add query-count/performance tests for key report endpoints.
2. Introduce async execution for non-critical side effects (for example alert delivery) when task infrastructure is added.
3. Add explicit select/prefetch tuning review for each report endpoint.
4. Consider streaming strategies for large export payloads.

## Chapter 39 Outcome
You can now evaluate the project’s current performance posture and prioritize optimizations without changing core behavior.
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

