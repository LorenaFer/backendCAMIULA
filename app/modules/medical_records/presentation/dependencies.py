"""Dependency injection factories for the Medical Records module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)
from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)
from app.modules.medical_records.infrastructure.repositories.sqlalchemy_form_schema_repository import (
    SQLAlchemyFormSchemaRepository,
)
from app.modules.medical_records.infrastructure.repositories.sqlalchemy_medical_record_repository import (
    SQLAlchemyMedicalRecordRepository,
)
from app.shared.database.session import get_db


def get_medical_record_repo(
    session: AsyncSession = Depends(get_db),
) -> MedicalRecordRepository:
    return SQLAlchemyMedicalRecordRepository(session)


def get_form_schema_repo(
    session: AsyncSession = Depends(get_db),
) -> FormSchemaRepository:
    return SQLAlchemyFormSchemaRepository(session)
