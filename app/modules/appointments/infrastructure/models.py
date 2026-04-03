"""SQLAlchemy models for the Appointments module."""

from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class AppointmentModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "appointments"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # 2. Relations (logical FKs — cross-module, no ForeignKey constraint)
    fk_patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    fk_doctor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    fk_specialty_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # 3. Domain
    appointment_date: Mapped[Optional[str]] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[Optional[str]] = mapped_column(Time, nullable=False)
    end_time: Mapped[Optional[str]] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_first_visit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 4. Business status
    appointment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default="pendiente",
        index=True,
    )

    # 5-8. status, created_at/by, updated_at/by, deleted_at/by via mixins
