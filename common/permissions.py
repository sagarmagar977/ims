from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRoles


READ_ONLY_ROLES = {
    UserRoles.FINANCE,
    UserRoles.AUDIT,
}

WRITE_ROLES = {
    UserRoles.SUPER_ADMIN,
    UserRoles.CENTRAL_ADMIN,
    UserRoles.CENTRAL_PROCUREMENT_STORE,
    UserRoles.PROVINCIAL_ADMIN,
    UserRoles.LOCAL_ADMIN,
    UserRoles.WARD_OFFICER,
}

WRITE_ROLE_MATRIX = {
    "office": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "category": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "custom-field-definition": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
    },
    "inventory-item": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "fixed-asset": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "consumable-stock-transaction": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
        UserRoles.WARD_OFFICER,
    },
    "item-assignment": {
        UserRoles.SUPER_ADMIN,
        UserRoles.CENTRAL_ADMIN,
        UserRoles.CENTRAL_PROCUREMENT_STORE,
        UserRoles.PROVINCIAL_ADMIN,
        UserRoles.LOCAL_ADMIN,
    },
    "inventory-audit-log": set(),
}


class IMSAccessPermission(BasePermission):
    """
    Role baseline from PRD:
    - Finance/Audit: read-only
    - Operational/admin roles: read-write
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if request.method in SAFE_METHODS:
            return bool(user.role)

        if user.role in READ_ONLY_ROLES:
            return False

        view_basename = getattr(view, "basename", None)
        if view_basename in WRITE_ROLE_MATRIX:
            return user.role in WRITE_ROLE_MATRIX[view_basename]

        return user.role in WRITE_ROLES
