# Chapter 24 — Deep Dive: `common/permissions.py` and `common/access.py`

## Learning Goals
- Understand write permission decisions and data visibility scoping.

## Reference Files
- `common/permissions.py`
- `common/access.py`

## Deep Dive Walkthrough

## 1) Permission model (`common/permissions.py`)
- Read-only roles: `FINANCE`, `AUDIT`.
- `WRITE_ROLE_MATRIX` maps API resources (viewset basenames) to allowed writer roles.
- `IMSAccessPermission.has_permission` logic:
  - unauthenticated -> deny,
  - staff/superuser -> allow,
  - safe methods -> allow if user has role,
  - write + read-only role -> deny,
  - write + mapped basename -> role must be listed,
  - fallback -> role must be in broad `WRITE_ROLES`.

## 2) Office scoping (`common/access.py`)
- `GLOBAL_ROLES`: unrestricted visibility.
- `SCOPED_ROLES`: subtree visibility.
- `get_descendant_office_ids` performs iterative office-tree expansion.
- `get_accessible_office_ids` returns:
  - `None` for unrestricted,
  - office-id list for scoped,
  - empty list for unsupported.
- `scope_queryset_by_user` applies `office_lookup__in` filter unless unrestricted.

## 3) Combined effect
- Permission controls action type (read/write).
- Scope controls data visibility within allowed actions.
- Together they enforce role behavior and office hierarchy boundaries.

## Chapter 24 Outcome
You can now explain exactly why a request is allowed or denied and why the returned queryset includes only certain offices.
