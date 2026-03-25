from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.doctor import Doctor
from app.modules.appointments.domain.entities.enums import DoctorStatus
from app.modules.appointments.domain.repositories.doctor_repository import (
    DoctorRepository,
)
from app.modules.appointments.infrastructure.models import (
    DoctorAvailabilityModel,
    DoctorModel,
    SpecialtyModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyDoctorRepository(DoctorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(
        model: DoctorModel,
        specialty_name: str = None,
        work_days: list = None,
    ) -> Doctor:
        return Doctor(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            user_id=model.fk_user_id,
            specialty_id=model.fk_specialty_id,
            doctor_status=model.doctor_status,
            specialty_name=specialty_name,
            work_days=work_days or [],
        )

    async def list_active(self) -> List[Doctor]:
        """Lista doctores activos con su especialidad. O(log n + k)."""
        stmt = (
            select(DoctorModel, SpecialtyModel.name)
            .join(SpecialtyModel, DoctorModel.fk_specialty_id == SpecialtyModel.id)
            .where(
                DoctorModel.doctor_status == DoctorStatus.ACTIVE.value,
                DoctorModel.status == RecordStatus.ACTIVE,
                SpecialtyModel.status == RecordStatus.ACTIVE,
            )
            .order_by(DoctorModel.last_name, DoctorModel.first_name)
            .limit(200)
        )
        result = await self._session.execute(stmt)
        return [
            self._to_entity(row[0], specialty_name=row[1]) for row in result.all()
        ]

    async def get_by_id(self, doctor_id: str) -> Optional[Doctor]:
        stmt = select(DoctorModel).where(
            DoctorModel.id == doctor_id,
            DoctorModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, user_id: str) -> Optional[Doctor]:
        stmt = select(DoctorModel).where(
            DoctorModel.fk_user_id == user_id,
            DoctorModel.status == RecordStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_options(self) -> List[Doctor]:
        """Doctores para selectores con días de trabajo. O(log n + k).

        Un solo query con JOIN a disponibilidad para obtener días únicos.
        """
        # Obtener doctores activos con especialidad
        stmt = (
            select(DoctorModel, SpecialtyModel.name)
            .join(SpecialtyModel, DoctorModel.fk_specialty_id == SpecialtyModel.id)
            .where(
                DoctorModel.doctor_status == DoctorStatus.ACTIVE.value,
                DoctorModel.status == RecordStatus.ACTIVE,
                SpecialtyModel.status == RecordStatus.ACTIVE,
            )
            .order_by(DoctorModel.last_name)
        )
        result = await self._session.execute(stmt)
        doctors_raw = result.all()

        if not doctors_raw:
            return []

        # Obtener días de trabajo para todos los doctores activos en un solo query
        doctor_ids = [row[0].id for row in doctors_raw]
        days_stmt = (
            select(
                DoctorAvailabilityModel.fk_doctor_id,
                DoctorAvailabilityModel.day_of_week,
            )
            .where(
                DoctorAvailabilityModel.fk_doctor_id.in_(doctor_ids),
                DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
            )
            .distinct()
        )
        days_result = await self._session.execute(days_stmt)
        days_map: dict[str, list[int]] = {}
        for doctor_id, day in days_result.all():
            days_map.setdefault(doctor_id, []).append(day)

        # Solo incluir doctores con al menos un bloque de disponibilidad
        doctors = []
        for model, specialty_name in doctors_raw:
            work_days = sorted(days_map.get(model.id, []))
            if work_days:
                doctors.append(self._to_entity(model, specialty_name, work_days))

        return doctors
