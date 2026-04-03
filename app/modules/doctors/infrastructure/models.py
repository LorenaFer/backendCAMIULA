"""
SQLAlchemy models for the Doctors module.

Tables: specialties, doctors, doctor_availability, doctor_exceptions.
All tables follow the project column standard:
    id -> fk_* -> domain -> {table_status} -> status -> audit
"""

from __future__ import annotations

import enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────


class DoctorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ─────────────────────────────────────────────────────────────
# SPECIALTIES
# ─────────────────────────────────────────────────────────────


class SpecialtyModel(Base, SoftDeleteMixin, AuditMixin):
    """Specialty catalog."""

    __tablename__ = "specialties"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 3. Domain
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # 5-8. status + audit from mixins

    # Relationships
    doctors: Mapped[list["DoctorModel"]] = relationship(
        back_populates="specialty", lazy="selectin"
    )


# ─────────────────────────────────────────────────────────────
# DOCTORS
# ─────────────────────────────────────────────────────────────


class DoctorModel(Base, SoftDeleteMixin, AuditMixin):
    """Doctor profile linked to a user and a specialty."""

    __tablename__ = "doctors"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relationships
    fk_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    fk_specialty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("specialties.id"), nullable=False
    )

    # 3. Domain
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 4. Business status
    doctor_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DoctorStatus.ACTIVE,
    )

    # 5-8. status + audit from mixins

    # Relationships
    specialty: Mapped["SpecialtyModel"] = relationship(
        back_populates="doctors", lazy="joined"
    )
    availability_blocks: Mapped[list["DoctorAvailabilityModel"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )
    exceptions: Mapped[list["DoctorExceptionModel"]] = relationship(
        back_populates="doctor", lazy="selectin"
    )


# ─────────────────────────────────────────────────────────────
# DOCTOR AVAILABILITY
# ─────────────────────────────────────────────────────────────


class DoctorAvailabilityModel(Base, SoftDeleteMixin, AuditMixin):
    """Recurring availability block for a doctor."""

    __tablename__ = "doctor_availability"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relationships
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False
    )

    # 3. Domain
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    slot_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # 5-8. status + audit from mixins

    # Relationships
    doctor: Mapped["DoctorModel"] = relationship(
        back_populates="availability_blocks", lazy="joined"
    )


# ─────────────────────────────────────────────────────────────
# DOCTOR EXCEPTIONS
# ─────────────────────────────────────────────────────────────


class DoctorExceptionModel(Base, SoftDeleteMixin, AuditMixin):
    """Single-day exception (absence) for a doctor."""

    __tablename__ = "doctor_exceptions"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # 2. Relationships
    fk_doctor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("doctors.id"), nullable=False
    )

    # 3. Domain
    exception_date: Mapped[Optional[str]] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500))

    # 5-8. status + audit from mixins

    # Relationships
    doctor: Mapped["DoctorModel"] = relationship(
        back_populates="exceptions", lazy="joined"
    )
