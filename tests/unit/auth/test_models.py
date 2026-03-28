"""Tests de compliance: orden de columnas en modelos auth."""

import pytest

from app.modules.auth.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
    UserRoleModel,
)
from app.shared.database.validators import validate_column_order


@pytest.mark.parametrize(
    "model",
    [UserModel, RoleModel, PermissionModel, RolePermissionModel, UserRoleModel],
    ids=lambda m: m.__tablename__,
)
def test_column_order_standard(model):
    """Verifica que cada modelo siga el estándar de BD."""
    violations = validate_column_order(model)
    assert violations == [], (
        f"Violaciones en {model.__tablename__}: {violations}"
    )
