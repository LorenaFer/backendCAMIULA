"""Dependency injection factories for the Doctors module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)
from app.modules.doctors.domain.repositories.doctor_repository import (
    DoctorRepository,
)
from app.modules.doctors.domain.repositories.exception_repository import (
    ExceptionRepository,
)
from app.modules.doctors.domain.repositories.specialty_repository import (
    SpecialtyRepository,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_availability_repository import (
    SQLAlchemyAvailabilityRepository,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_doctor_repository import (
    SQLAlchemyDoctorRepository,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_exception_repository import (
    SQLAlchemyExceptionRepository,
)
from app.modules.doctors.infrastructure.repositories.sqlalchemy_specialty_repository import (
    SQLAlchemySpecialtyRepository,
)
from app.shared.database.session import get_db


def get_doctor_repo(
    session: AsyncSession = Depends(get_db),
) -> DoctorRepository:
    return SQLAlchemyDoctorRepository(session)


def get_specialty_repo(
    session: AsyncSession = Depends(get_db),
) -> SpecialtyRepository:
    return SQLAlchemySpecialtyRepository(session)


def get_availability_repo(
    session: AsyncSession = Depends(get_db),
) -> AvailabilityRepository:
    return SQLAlchemyAvailabilityRepository(session)


def get_exception_repo(
    session: AsyncSession = Depends(get_db),
) -> ExceptionRepository:
    return SQLAlchemyExceptionRepository(session)
