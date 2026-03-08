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
