"""
Mixins estándar para modelos SQLAlchemy.

Todas las tablas del proyecto DEBEN seguir este orden de columnas:

    ┌─────────┬──────────────────────┬──────────────────────────────────────┐
    │ Orden   │ Grupo                │ Columnas                             │
    ├─────────┼──────────────────────┼──────────────────────────────────────┤
    │ 1       │ Identidad            │ id                                   │
    │ 2       │ Relaciones           │ fk_*                                 │
    │ 3       │ Dominio              │ {datos propios de la tabla}          │
    │ 4       │ Lógica de negocio    │ {table_status} (ej: patient_status)  │
    │ 5       │ Control técnico      │ status (A / I / T)                   │
    │ 6       │ Auditoría creación   │ created_at, created_by               │
    │ 7       │ Auditoría edición    │ updated_at, updated_by               │
    │ 8       │ Auditoría eliminación│ deleted_at, deleted_by               │
    └─────────┴──────────────────────┴──────────────────────────────────────┘

    Razón: parear timestamp + actor por cada acción de auditoría facilita
    la lectura y los deleted_* quedan al final porque solo se consultan
    en procesos de recuperación.

Uso:
    from app.shared.database.base import Base
    from app.shared.database.mixins import AuditMixin, SoftDeleteMixin

    class PatientModel(Base, SoftDeleteMixin, AuditMixin):
        __tablename__ = "patients"

        id: Mapped[str] = mapped_column(String(36), primary_key=True)
        # fk_* ...
        # {datos} ...
        # {table_status} ...
        # status, created_at, created_by, etc. vienen de los mixins
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column


# ---------------------------------------------------------------------------
# Enum: status técnico del registro (Grupo 5 — Control)
# ---------------------------------------------------------------------------


class RecordStatus(str, enum.Enum):
    """Status técnico de cualquier registro en la base de datos.

    A = Active  — registro vigente y visible.
    I = Inactive — registro deshabilitado pero recuperable.
    T = Trash   — marcado para eliminación (soft-delete).
    """

    ACTIVE = "A"
    INACTIVE = "I"
    TRASH = "T"


# ---------------------------------------------------------------------------
# Mixin: Control técnico (Grupo 5)
# ---------------------------------------------------------------------------


class SoftDeleteMixin:
    """Agrega la columna `status` para control técnico del registro.

    Posición: después de {table_status}, antes de auditoría.
    """

    status: Mapped[str] = mapped_column(
        Enum(
            RecordStatus,
            name="record_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=RecordStatus.ACTIVE,
        server_default=RecordStatus.ACTIVE.value,
        nullable=False,
        index=True,
        comment="Status técnico: A=active, I=inactive, T=trash",
    )


# ---------------------------------------------------------------------------
# Mixin: Auditoría — parejas (timestamp + actor) (Grupos 6, 7, 8)
# ---------------------------------------------------------------------------


class AuditMixin:
    """Agrega las 3 parejas de auditoría: creación, edición, eliminación.

    Cada acción tiene su timestamp y el UUID del usuario que la ejecutó.
    Esto facilita la trazabilidad sin consultas JOIN adicionales.
    """

    # --- Grupo 6: Auditoría de creación ---

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="UUID del usuario que creó el registro",
    )

    # --- Grupo 7: Auditoría de edición ---

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="UUID del usuario que actualizó el registro",
    )

    # --- Grupo 8: Auditoría de eliminación (solo en soft-delete) ---

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    deleted_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="UUID del usuario que eliminó (soft-delete) el registro",
    )
