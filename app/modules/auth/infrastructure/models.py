from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class UserModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "users"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 3: Dominio ---
    external_auth: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment='Proveedores externos: {"auth0": {"sub": "..."}, "keycloak": {"sub": "..."}}',
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # --- Grupo 4: Lógica de negocio ---
    user_status: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="PENDING"
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---


class RoleModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "roles"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 3: Dominio ---
    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---


class PermissionModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "permissions"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 3: Dominio ---
    code: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    module: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---


class RolePermissionModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "fk_role_id",
            "fk_permission_id",
            name="uq_role_permissions_role_permission",
        ),
        Index("ix_role_permissions_role_status", "fk_role_id", "status"),
    )

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id"), nullable=False, index=True
    )
    fk_permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("permissions.id"), nullable=False, index=True
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---


class UserRoleModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint(
            "fk_user_id", "fk_role_id", name="uq_user_roles_user_role"
        ),
        Index("ix_user_roles_user_status", "fk_user_id", "status"),
    )

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    fk_role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id"), nullable=False, index=True
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---
