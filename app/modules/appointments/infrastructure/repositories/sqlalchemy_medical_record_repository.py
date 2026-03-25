from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.medical_record import MedicalRecord
from app.modules.appointments.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)
from app.modules.appointments.infrastructure.models import MedicalRecordModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyMedicalRecordRepository(MedicalRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: MedicalRecordModel) -> MedicalRecord:
        return MedicalRecord(
            id=model.id,
            appointment_id=model.fk_appointment_id,
            patient_id=model.fk_patient_id,
            doctor_id=model.fk_doctor_id,
            evaluation=model.evaluation,
            is_prepared=model.is_prepared,
            prepared_at=model.prepared_at,
            prepared_by=model.prepared_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_appointment_id(
        self, appointment_id: str
    ) -> Optional[MedicalRecord]:
        stmt = select(MedicalRecordModel).where(
            MedicalRecordModel.fk_appointment_id == appointment_id,
            MedicalRecordModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, record_id: str) -> Optional[MedicalRecord]:
        stmt = select(MedicalRecordModel).where(
            MedicalRecordModel.id == record_id,
            MedicalRecordModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def upsert(self, record: MedicalRecord) -> MedicalRecord:
        """Upsert por appointment_id."""
        existing = await self._session.execute(
            select(MedicalRecordModel).where(
                MedicalRecordModel.fk_appointment_id == record.appointment_id,
                MedicalRecordModel.status == RecordStatus.ACTIVE,
            )
        )
        model = existing.scalar_one_or_none()

        if model is None:
            model = MedicalRecordModel(
                id=record.id or str(uuid4()),
                fk_appointment_id=record.appointment_id,
                fk_patient_id=record.patient_id,
                fk_doctor_id=record.doctor_id,
                evaluation=record.evaluation,
            )
            self._session.add(model)
        else:
            model.evaluation = record.evaluation

        await self._session.flush()
        return self._to_entity(model)

    async def mark_prepared(self, record_id: str, prepared_by: str) -> None:
        stmt = select(MedicalRecordModel).where(
            MedicalRecordModel.id == record_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.is_prepared = True
            model.prepared_at = datetime.now(timezone.utc)
            model.prepared_by = prepared_by
            await self._session.flush()
