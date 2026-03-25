from datetime import date, datetime, time
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class SpecialtyModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "specialties"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 3: Dominio ---
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # --- Grupos 5-8: Mixins ---


class DoctorModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "doctors"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    fk_specialty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("specialties.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # --- Grupo 4: Lógica de negocio ---
    doctor_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="ACTIVE"
    )

    # --- Grupos 5-8: Mixins ---


class DoctorAvailabilityModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "doctor_availability"
    __table_args__ = (
        Index("ix_doctor_availability_doctor_day", "fk_doctor_id", "day_of_week"),
    )

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Grupos 5-8: Mixins ---


class DoctorExceptionModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "doctor_exceptions"
    __table_args__ = (
        Index("ix_doctor_exceptions_doctor_date", "fk_doctor_id", "exception_date"),
    )

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    exception_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Grupos 5-8: Mixins ---


class AppointmentModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_date_doctor", "appointment_date", "fk_doctor_id"),
        Index("ix_appointments_patient_status", "fk_patient_id", "appointment_status"),
    )

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False, index=True
    )
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False, index=True
    )
    fk_specialty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("specialties.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_first_visit: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Grupo 4: Lógica de negocio ---
    appointment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING", index=True
    )

    # --- Grupos 5-8: Mixins ---


class MedicalRecordModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "medical_records"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones ---
    fk_appointment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("appointments.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    fk_patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), nullable=False, index=True
    )
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False, index=True
    )

    # --- Grupo 3: Dominio ---
    evaluation: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_prepared: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    prepared_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    prepared_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # --- Grupos 5-8: Mixins ---
