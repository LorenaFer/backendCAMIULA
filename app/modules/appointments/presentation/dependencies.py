"""Dependency injection factories for the Appointments module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)
from app.modules.appointments.infrastructure.repositories.sqlalchemy_appointment_repository import (
    SQLAlchemyAppointmentRepository,
)
from app.modules.doctors.domain.repositories.availability_reader import (
    AvailabilityReader,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_availability_reader import (
    SQLAlchemyAvailabilityReader,
)
from app.shared.database.session import get_db


def get_appointment_repo(
    session: AsyncSession = Depends(get_db),
) -> AppointmentRepository:
    return SQLAlchemyAppointmentRepository(session)


def get_availability_reader(
    session: AsyncSession = Depends(get_db),
) -> AvailabilityReader:
    return SQLAlchemyAvailabilityReader(session)
