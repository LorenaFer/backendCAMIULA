"""Dependency injection factories for the Patients module.

This is the ONLY presentation file allowed to import from infrastructure.
All routers must use Depends() with these factories instead of
instantiating repositories directly.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import (
    SQLAlchemyPatientRepository,
)
from app.shared.database.session import get_db


def get_patient_repo(
    session: AsyncSession = Depends(get_db),
) -> PatientRepository:
    return SQLAlchemyPatientRepository(session)
