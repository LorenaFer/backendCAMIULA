"""SQLAlchemy implementation of the Doctor repository."""

from typing import List, Optional

from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.doctors.domain.entities.doctor import Doctor
from app.modules.doctors.domain.repositories.doctor_repository import (
    DoctorRepository,
)
from app.modules.doctors.infrastructure.models import (
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
        specialty_name: Optional[str] = None,
        work_days: Optional[list] = None,
    ) -> Doctor:
        return Doctor(
            id=model.id,
            fk_user_id=model.fk_user_id,
            fk_specialty_id=model.fk_specialty_id,
            first_name=model.first_name,
            last_name=model.last_name,
            doctor_status=model.doctor_status,
            specialty_name=specialty_name,
            work_days=work_days or [],
            status=model.status if isinstance(model.status, str) else model.status.value,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_all_active(self) -> List[Doctor]:
        result = await self._session.execute(
            select(DoctorModel)
            .options(joinedload(DoctorModel.specialty))
            .where(DoctorModel.status == RecordStatus.ACTIVE)
            .order_by(DoctorModel.last_name, DoctorModel.first_name)
        )
        doctors = result.unique().scalars().all()
        return [
            self._to_entity(
                d,
                specialty_name=d.specialty.name if d.specialty else None,
            )
            for d in doctors
        ]

    async def find_options(self) -> List[Doctor]:
        """Lightweight list with computed work_days from doctor_availability."""
        result = await self._session.execute(
            select(DoctorModel)
            .options(joinedload(DoctorModel.specialty))
            .where(
                DoctorModel.status == RecordStatus.ACTIVE,
                DoctorModel.doctor_status.in_(["active", "ACTIVE"]),
            )
            .order_by(DoctorModel.last_name, DoctorModel.first_name)
        )
        doctors = result.unique().scalars().all()

        entities = []
        for d in doctors:
            # Subquery for distinct work days
            days_result = await self._session.execute(
                select(distinct(DoctorAvailabilityModel.day_of_week))
                .where(
                    DoctorAvailabilityModel.fk_doctor_id == d.id,
                    DoctorAvailabilityModel.status == RecordStatus.ACTIVE,
                )
                .order_by(DoctorAvailabilityModel.day_of_week)
            )
            work_days = [row[0] for row in days_result.all()]
            entities.append(
                self._to_entity(
                    d,
                    specialty_name=d.specialty.name if d.specialty else None,
                    work_days=work_days,
                )
            )
        return entities

    async def find_by_id(self, id: str) -> Optional[Doctor]:
        result = await self._session.execute(
            select(DoctorModel)
            .options(joinedload(DoctorModel.specialty))
            .where(
                DoctorModel.id == id,
                DoctorModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(
            model,
            specialty_name=model.specialty.name if model.specialty else None,
        )
