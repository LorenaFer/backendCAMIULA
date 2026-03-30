"""Modelos SQLAlchemy del módulo de pacientes."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 3. Dominio
    nhm: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    cedula: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido: Mapped[str] = mapped_column(String(120), nullable=False)
    sexo: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    lugar_nacimiento: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    edad: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estado_civil: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    procedencia: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    direccion_habitacion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    profesion: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    ocupacion_actual: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    direccion_trabajo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    clasificacion_economica: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    relacion_univ: Mapped[str] = mapped_column(String(20), nullable=False, default="tercero")
    parentesco: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    titular_nhm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    datos_medicos: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    contacto_emergencia: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    es_nuevo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # 4. Lógica de negocio
    patient_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="active")


class PatientHistoryEntryModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patient_history_entries"

    # 1. Identidad
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relaciones
    fk_patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    # FK lógica hacia appointments
    fk_appointment_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    # 3. Dominio
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    especialidad: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    doctor_nombre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    diagnostico_descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    diagnostico_cie10: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 4. Lógica de negocio
    history_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="recorded")
