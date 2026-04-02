"""SQLAlchemy models for the Patients module."""

from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # 2. Relations
    fk_holder_patient_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )

    # 3. Domain
    nhm: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )
    cedula: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sex: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    birth_place: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    home_address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    profession: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_occupation: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    work_address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    economic_classification: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    university_relation: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    family_relationship: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    medical_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_new: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # 4. Business logic
    patient_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", server_default="active", index=True
    )

    # 5-8. status, created_at/by, updated_at/by, deleted_at/by via mixins
