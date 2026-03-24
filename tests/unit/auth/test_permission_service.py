"""Tests unitarios para PermissionService — lógica pura, sin BD."""

from app.modules.auth.domain.services.permission_service import PermissionService


class TestHasPermission:
    def test_user_has_permission(self):
        perms = {"patients:read", "patients:create", "profile:read"}
        assert PermissionService.has_permission(perms, "patients:read") is True

    def test_user_lacks_permission(self):
        perms = {"patients:read", "profile:read"}
        assert PermissionService.has_permission(perms, "users:delete") is False

    def test_empty_permissions(self):
        assert PermissionService.has_permission(set(), "anything") is False


class TestHasAnyPermission:
    def test_has_one_of_many(self):
        perms = {"patients:read"}
        required = {"patients:read", "patients:create"}
        assert PermissionService.has_any_permission(perms, required) is True

    def test_has_none_of_required(self):
        perms = {"profile:read"}
        required = {"patients:read", "patients:create"}
        assert PermissionService.has_any_permission(perms, required) is False


class TestHasAllPermissions:
    def test_has_all(self):
        perms = {"patients:read", "patients:create", "profile:read"}
        required = {"patients:read", "patients:create"}
        assert PermissionService.has_all_permissions(perms, required) is True

    def test_missing_one(self):
        perms = {"patients:read", "profile:read"}
        required = {"patients:read", "patients:create"}
        assert PermissionService.has_all_permissions(perms, required) is False


class TestMergeRolePermissions:
    def test_merge_multiple_roles(self):
        role1 = {"patients:read", "profile:read"}
        role2 = {"patients:read", "patients:create", "users:read"}
        merged = PermissionService.merge_role_permissions([role1, role2])
        assert merged == {"patients:read", "patients:create", "profile:read", "users:read"}

    def test_merge_empty(self):
        assert PermissionService.merge_role_permissions([]) == set()

    def test_merge_single_role(self):
        perms = {"a", "b"}
        assert PermissionService.merge_role_permissions([perms]) == perms
