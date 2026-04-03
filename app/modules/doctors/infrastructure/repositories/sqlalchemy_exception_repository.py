"""SQLAlchemy implementation of the Exception repository."""

from datetime import date as date_type
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.doctors.domain.entities.doctor_exception import DoctorException
from app.modules.doctors.domain.repositories.exception_repository import (
    ExceptionRepository,
)
from app.modules.doctors.infrastructure.models import DoctorExceptionModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyExceptionRepository(ExceptionRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: DoctorExceptionModel) -> DoctorException:
        return DoctorException(
            id=model.id,
            fk_doctor_id=model.fk_doctor_id,
            exception_date=model.exception_date.isoformat() if hasattr(model.exception_date, 'isoformat') else model.exception_date,
            reason=model.reason,
            status=model.status if isinstance(model.status, str) else model.status.value,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_by_doctor_and_date(
        self, doctor_id: str, exception_date: Optional[str] = None
    ) -> List[DoctorException]:
        q = (
            select(DoctorExceptionModel)
            .where(
                DoctorExceptionModel.fk_doctor_id == doctor_id,
                DoctorExceptionModel.status == RecordStatus.ACTIVE,
            )
            .order_by(DoctorExceptionModel.exception_date)
        )
        if exception_date:
            d = date_type.fromisoformat(exception_date) if isinstance(exception_date, str) else exception_date
            q = q.where(DoctorExceptionModel.exception_date == d)

        result = await self._session.execute(q)
        return [self._to_entity(m) for m in result.scalars().all()]
