"""Dependency injection factories for the Appointments module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_appointment_repository import (
    SQLAlchemyAppointmentRepository,
)
from app.shared.database.session import get_db


def get_appointment_repo(
    session: AsyncSession = Depends(get_db),
) -> AppointmentRepository:
    return SQLAlchemyAppointmentRepository(session)
