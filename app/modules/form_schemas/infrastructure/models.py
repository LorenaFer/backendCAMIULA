"""SQLAlchemy model para form_schemas.

Nota: Esta tabla usa un PK semántico VARCHAR (ej: "medicina-general-v1")
en lugar de UUID, ya que el ID forma parte del protocolo frontend-backend.
El campo id es asignado por la aplicación, no generado por la DB.
"""
from typing import Any, Dict

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class FormSchemaModel(Base, SoftDeleteMixin, AuditMixin):
    """Schema de formulario dinámico por especialidad.

    Orden de columnas (según estándar 06-estandar-base-de-datos.md):
    1. id (identidad/PK semántico)
    2. specialty_id, specialty_name (dominio — relación lógica con especialidades)
    3. version, schema_json (dominio)
    5. status           — de SoftDeleteMixin
    6. created_at, created_by — de AuditMixin
    7. updated_at, updated_by — de AuditMixin
    8. deleted_at, deleted_by — de AuditMixin
    """

    __tablename__ = "form_schemas"
    __table_args__ = (
        Index("ix_form_schemas_specialty_id", "specialty_id"),
    )

    # --- Grupo 1: Identidad (PK semántico) ---
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # --- Grupo 2: Relación con especialidad ---
    specialty_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    specialty_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # --- Grupo 3: Dominio ---
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    schema_json: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Grupos 5-8: status, created_at/by, updated_at/by, deleted_at/by
    # vienen de SoftDeleteMixin y AuditMixin
