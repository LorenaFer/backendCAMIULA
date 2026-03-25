from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_holder_patient_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )

    # --- Grupo 3: Dominio ---
    nhm: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    cedula: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sex: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    birth_date: Mapped[Optional[Any]] = mapped_column(Date, nullable=True)
    birth_place: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    home_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    profession: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_occupation: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    work_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    economic_classification: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    university_relation: Mapped[str] = mapped_column(String(30), nullable=False)
    family_relationship: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True
    )
    medical_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=None
    )
    emergency_contact: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=None
    )
    is_new: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    # --- Grupo 4: Lógica de negocio ---
    patient_status: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="ACTIVE", index=True
    )

    # --- Grupos 5-8: SoftDeleteMixin + AuditMixin ---
