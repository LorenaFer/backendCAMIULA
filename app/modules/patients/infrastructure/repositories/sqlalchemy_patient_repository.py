from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.domain.entities.enums import PatientStatus
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyPatientRepository(PatientRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: PatientModel) -> Patient:
        return Patient(
            id=model.id,
            nhm=model.nhm,
            cedula=model.cedula,
            first_name=model.first_name,
            last_name=model.last_name,
            sex=model.sex,
            birth_date=model.birth_date,
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
            holder_patient_id=model.fk_holder_patient_id,
            medical_data=model.medical_data,
            emergency_contact=model.emergency_contact,
            is_new=model.is_new,
            patient_status=model.patient_status or PatientStatus.ACTIVE.value,
            created_at=model.created_at,
        )

    async def create(self, patient: Patient) -> Patient:
        model = PatientModel(
            id=patient.id or str(uuid4()),
            fk_holder_patient_id=patient.holder_patient_id,
            nhm=patient.nhm,
            cedula=patient.cedula,
            first_name=patient.first_name,
            last_name=patient.last_name,
            sex=patient.sex,
            birth_date=patient.birth_date,
            birth_place=patient.birth_place,
            marital_status=patient.marital_status,
            religion=patient.religion,
            origin=patient.origin,
            home_address=patient.home_address,
            phone=patient.phone,
            profession=patient.profession,
            current_occupation=patient.current_occupation,
            work_address=patient.work_address,
            economic_classification=patient.economic_classification,
            university_relation=patient.university_relation,
            family_relationship=patient.family_relationship,
            medical_data=patient.medical_data,
            emergency_contact=patient.emergency_contact,
            is_new=patient.is_new,
            patient_status=patient.patient_status,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(
            PatientModel.id == patient_id,
            PatientModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_cedula(self, cedula: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(
            PatientModel.cedula == cedula,
            PatientModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_nhm(self, nhm: int) -> Optional[Patient]:
        stmt = select(PatientModel).where(
            PatientModel.nhm == nhm,
            PatientModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_max_nhm(self) -> int:
        """O(log n) — MAX sobre índice único."""
        stmt = (
            select(func.coalesce(func.max(PatientModel.nhm), 0))
            .where(PatientModel.status == RecordStatus.ACTIVE)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def next_nhm(self) -> int:
        """Atómico: usa secuencia PostgreSQL. O(1)."""
        result = await self._session.execute(text("SELECT nextval('nhm_seq')"))
        return result.scalar_one()

    async def exists_by_cedula(self, cedula: str) -> bool:
        """O(log n) — COUNT con índice."""
        stmt = (
            select(func.count())
            .select_from(PatientModel)
            .where(
                PatientModel.cedula == cedula,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
