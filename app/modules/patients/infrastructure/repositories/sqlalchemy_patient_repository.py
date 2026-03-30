"""Repositorio SQLAlchemy para pacientes."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.domain.entities.patient import Patient, PatientHistoryEntry
from app.modules.patients.domain.repositories.patient_repository import PatientRepository
from app.modules.patients.infrastructure.models import (
    PatientHistoryEntryModel,
    PatientModel,
)
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
            nombre=model.nombre,
            apellido=model.apellido,
            sexo=model.sexo,
            fecha_nacimiento=model.fecha_nacimiento,
            lugar_nacimiento=model.lugar_nacimiento,
            edad=model.edad,
            estado_civil=model.estado_civil,
            religion=model.religion,
            procedencia=model.procedencia,
            direccion_habitacion=model.direccion_habitacion,
            telefono=model.telefono,
            profesion=model.profesion,
            ocupacion_actual=model.ocupacion_actual,
            direccion_trabajo=model.direccion_trabajo,
            clasificacion_economica=model.clasificacion_economica,
            relacion_univ=model.relacion_univ,
            parentesco=model.parentesco,
            titular_nhm=model.titular_nhm,
            datos_medicos=model.datos_medicos or {},
            contacto_emergencia=model.contacto_emergencia or {},
            es_nuevo=model.es_nuevo,
            created_at=model.created_at.isoformat() if model.created_at else None,
        )

    @staticmethod
    def _to_history_entity(model: PatientHistoryEntryModel) -> PatientHistoryEntry:
        return PatientHistoryEntry(
            id=model.id,
            fecha=model.fecha.isoformat(),
            especialidad=model.especialidad,
            doctor_nombre=model.doctor_nombre,
            diagnostico_descripcion=model.diagnostico_descripcion,
            diagnostico_cie10=model.diagnostico_cie10,
        )

    async def find_by_cedula(self, cedula: str) -> Optional[Patient]:
        result = await self._session.execute(
            select(PatientModel).where(
                PatientModel.cedula == cedula,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_nhm(self, nhm: int) -> Optional[Patient]:
        result = await self._session.execute(
            select(PatientModel).where(
                PatientModel.nhm == nhm,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_id(self, patient_id: str) -> Optional[Patient]:
        result = await self._session.execute(
            select(PatientModel).where(
                PatientModel.id == patient_id,
                PatientModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_next_nhm(self) -> int:
        result = await self._session.execute(select(func.max(PatientModel.nhm)))
        current = result.scalar_one_or_none()
        return (current or 100000) + 1

    async def create(self, data: dict, created_by: str) -> Patient:
        model = PatientModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_history(
        self,
        patient_id: str,
        limit: int,
        exclude_appointment_id: Optional[str],
    ) -> list[PatientHistoryEntry]:
        stmt = (
            select(PatientHistoryEntryModel)
            .where(
                PatientHistoryEntryModel.fk_patient_id == patient_id,
                PatientHistoryEntryModel.status == RecordStatus.ACTIVE,
            )
            .order_by(PatientHistoryEntryModel.fecha.desc())
            .limit(limit)
        )

        if exclude_appointment_id:
            stmt = stmt.where(
                PatientHistoryEntryModel.fk_appointment_id != exclude_appointment_id
            )

        result = await self._session.execute(stmt)
        return [self._to_history_entity(row) for row in result.scalars().all()]
