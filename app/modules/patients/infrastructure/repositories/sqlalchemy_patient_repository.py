"""SQLAlchemy implementation of the patient repository."""

from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyPatientRepository(PatientRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: PatientModel) -> Patient:
        return Patient(
            id=model.id,
            cedula=model.cedula,
            nhm=model.nhm,
            first_name=model.first_name,
            last_name=model.last_name,
            sex=model.sex,
            birth_date=(
                model.birth_date.isoformat() if model.birth_date else None
            ),
            birth_place=model.birth_place,
            marital_status=model.marital_status,
            religion=model.religion,
            origin=model.origin,
            home_address=model.home_address,
            phone=model.phone,
            profession=model.profession,
            current_occupation=model.current_occupation,
            work_address=model.work_address,
            economic_classification=model.economic_classification,
            university_relation=model.university_relation,
            family_relationship=model.family_relationship,
            fk_holder_patient_id=model.fk_holder_patient_id,
            medical_data=model.medical_data or {},
            emergency_contact=model.emergency_contact,
            is_new=model.is_new,
            patient_status=model.patient_status,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    # ── Queries ───────────────────────────────────────────────

    async def find_all(
        self, page: int, page_size: int
    ) -> tuple[list[Patient], int]:
        base = select(PatientModel).where(
            PatientModel.status == RecordStatus.ACTIVE
        )

        count_q = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(
            base.order_by(PatientModel.last_name, PatientModel.first_name)
            .offset(offset)
            .limit(page_size)
        )
        return [self._to_entity(row) for row in result.scalars().all()], total

    async def find_by_nhm(self, nhm: int) -> Optional[Patient]:
        result = await self._session.execute(
            select(PatientModel).where(
                PatientModel.nhm == nhm,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_cedula(self, cedula: str) -> Optional[Patient]:
        result = await self._session.execute(
            select(PatientModel).where(
                PatientModel.cedula == cedula,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_max_nhm(self) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(PatientModel.nhm), 0)).where(
                PatientModel.status == RecordStatus.ACTIVE
            )
        )
        return result.scalar_one()

    async def get_next_nhm(self) -> int:
        """Gets the next NHM safely with advisory lock to prevent race conditions."""
        # Advisory lock on a fixed key to serialize NHM generation
        await self._session.execute(text("SELECT pg_advisory_xact_lock(1001)"))
        result = await self._session.execute(
            text(
                "SELECT COALESCE(MAX(nhm), 0) + 1 AS next_nhm "
                "FROM patients "
                "WHERE status = 'A'"
            )
        )
        return result.scalar_one()

    # ── Writes ────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Patient:
        # Convert birth_date string to date object for asyncpg
        if isinstance(data.get("birth_date"), str):
            from datetime import date as date_type
            data["birth_date"] = date_type.fromisoformat(data["birth_date"])

        model = PatientModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)
