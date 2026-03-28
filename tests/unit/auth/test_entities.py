"""Tests unitarios para entidades de dominio."""

from app.modules.auth.domain.entities.enums import UserStatus
from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User


class TestUserEntity:
    def test_create_user(self):
        user = User(email="test@test.com", full_name="Test")
        assert user.email == "test@test.com"
        assert user.full_name == "Test"
        assert len(user.id) == 36  # UUID
        assert user.user_status == UserStatus.PENDING.value
        assert user.roles == []
        assert user.permissions == set()

    def test_get_external_sub_exists(self):
        user = User(
            email="test@test.com",
            full_name="Test",
            external_auth={"auth0": {"sub": "auth0|abc123"}},
        )
        assert user.get_external_sub("auth0") == "auth0|abc123"

    def test_get_external_sub_missing_provider(self):
        user = User(
            email="test@test.com",
            full_name="Test",
            external_auth={"auth0": {"sub": "abc"}},
        )
        assert user.get_external_sub("keycloak") is None

    def test_get_external_sub_no_auth(self):
        user = User(email="test@test.com", full_name="Test")
        assert user.get_external_sub("auth0") is None


class TestRoleEntity:
    def test_create_role(self):
        role = Role(name="admin", description="Full access")
        assert role.name == "admin"
        assert role.permissions == []


class TestPermissionEntity:
    def test_create_permission(self):
        perm = Permission(code="patients:read", module="patients")
        assert perm.code == "patients:read"
        assert perm.module == "patients"
