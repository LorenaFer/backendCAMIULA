"""SQLAlchemy implementation of the Medical Record repository."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.infrastructure.models import AppointmentModel
from app.modules.doctors.infrastructure.models import DoctorModel, SpecialtyModel
from app.modules.medical_records.domain.entities.medical_record import MedicalRecord
from app.modules.medical_records.domain.repositories.medical_record_repository import (
    MedicalRecordRepository,
)
from app.modules.medical_records.infrastructure.models import MedicalRecordModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyMedicalRecordRepository(MedicalRecordRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # ORM -> domain entity
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: MedicalRecordModel) -> MedicalRecord:
        return MedicalRecord(
            id=model.id,
            fk_appointment_id=model.fk_appointment_id,
            fk_patient_id=model.fk_patient_id,
            fk_doctor_id=model.fk_doctor_id,
            evaluation=model.evaluation,
            is_prepared=model.is_prepared,
            prepared_at=model.prepared_at.isoformat() if model.prepared_at else None,
            prepared_by=model.prepared_by,
            schema_id=model.schema_id,
            schema_version=model.schema_version,
            status=model.status.value if hasattr(model.status, "value") else model.status,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
            updated_by=model.updated_by,
        )

    # ──────────────────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────────────────

    async def find_by_appointment_id(self, appointment_id: str) -> Optional[MedicalRecord]:
        result = await self._session.execute(
            select(MedicalRecordModel).where(
                MedicalRecordModel.fk_appointment_id == appointment_id,
                MedicalRecordModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_id(self, record_id: str) -> Optional[MedicalRecord]:
        result = await self._session.execute(
            select(MedicalRecordModel).where(
                MedicalRecordModel.id == record_id,
                MedicalRecordModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def patient_history(
        self,
        patient_id: str,
        limit: int,
        exclude_id: Optional[str],
    ) -> List[dict]:
        q = (
            select(
                MedicalRecordModel.id,
                AppointmentModel.appointment_date,
                SpecialtyModel.name.label("specialty"),
                DoctorModel.first_name,
                DoctorModel.last_name,
                MedicalRecordModel.evaluation,
            )
            .join(
                AppointmentModel,
                AppointmentModel.id == MedicalRecordModel.fk_appointment_id,
            )
            .join(
                DoctorModel,
                DoctorModel.id == MedicalRecordModel.fk_doctor_id,
            )
            .join(
                SpecialtyModel,
                SpecialtyModel.id == DoctorModel.fk_specialty_id,
            )
            .where(
                MedicalRecordModel.fk_patient_id == patient_id,
                MedicalRecordModel.status == RecordStatus.ACTIVE,
            )
        )

        if exclude_id:
            q = q.where(MedicalRecordModel.id != exclude_id)

        q = q.order_by(AppointmentModel.appointment_date.desc()).limit(limit)

        result = await self._session.execute(q)
        rows = result.all()

        history = []
        for row in rows:
            evaluation = row.evaluation or {}
            diagnosis = evaluation.get("diagnosis", {}) if isinstance(evaluation, dict) else {}
            history.append({
                "id": row.id,
                "date": row.appointment_date.isoformat() if row.appointment_date else None,
                "specialty": row.specialty,
                "doctor_name": f"{row.first_name} {row.last_name}",
                "diagnosis_description": diagnosis.get("description"),
                "diagnosis_code": diagnosis.get("code"),
            })
        return history

    # ──────────────────────────────────────────────────────────
    # Writes
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> MedicalRecord:
        model = MedicalRecordModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, record_id: str, data: dict, updated_by: str) -> MedicalRecord:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(MedicalRecordModel)
            .where(MedicalRecordModel.id == record_id)
            .values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(record_id)

    async def mark_prepared(self, record_id: str, prepared_by: str) -> MedicalRecord:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(MedicalRecordModel)
            .where(MedicalRecordModel.id == record_id)
            .values(
                is_prepared=True,
                prepared_at=now,
                prepared_by=prepared_by,
                updated_at=now,
                updated_by=prepared_by,
            )
        )
        await self._session.flush()
        return await self.find_by_id(record_id)
