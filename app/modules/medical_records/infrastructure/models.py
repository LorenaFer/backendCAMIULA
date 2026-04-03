"""SQLAlchemy models for the Medical Records module.

Tables: medical_records, form_schemas.
All tables follow the project column standard:
    id -> fk_* -> domain -> status -> audit

FK cross-module (appointments, patients, doctors) are logical -- no constraint.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


# -----------------------------------------------------------------
# MEDICAL RECORDS
# -----------------------------------------------------------------


class MedicalRecordModel(Base, SoftDeleteMixin, AuditMixin):
    """Medical record tied to a single appointment."""

    __tablename__ = "medical_records"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # 2. Relations (logical FKs -- cross-module, no ForeignKey constraint)
    fk_appointment_id: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Domain
    evaluation: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_prepared: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    prepared_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    prepared_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    schema_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    schema_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 5-8. status, created_at/by, updated_at/by, deleted_at/by via mixins


# -----------------------------------------------------------------
# FORM SCHEMAS
# -----------------------------------------------------------------


class FormSchemaModel(Base, SoftDeleteMixin, AuditMixin):
    """Dynamic form schema for a given specialty."""

    __tablename__ = "form_schemas"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # 2. Relations
    specialty_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # 3. Domain
    specialty_name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # 5-8. status, created_at/by, updated_at/by, deleted_at/by via mixins
