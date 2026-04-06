"""Use case: list appointments with filters and pagination."""

from typing import List, Optional, Tuple

from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class ListAppointments:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        page: int,
        page_size: int,
        fecha: Optional[str] = None,
        doctor_id: Optional[str] = None,
        especialidad_id: Optional[str] = None,
        estado: Optional[str] = None,
        q: Optional[str] = None,
        fk_patient_id: Optional[str] = None,
    ) -> Tuple[List[Appointment], int]:
        return await self._repo.find_all(
            page=page,
            page_size=page_size,
            fecha=fecha,
            doctor_id=doctor_id,
            especialidad_id=especialidad_id,
            estado=estado,
            q=q,
            fk_patient_id=fk_patient_id,
        )


class ListDoctorMonthAppointments:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: str,
        year: int,
        month: int,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        return await self._repo.find_by_doctor_and_month(
            doctor_id=doctor_id,
            year=year,
            month=month,
            exclude_cancelled=exclude_cancelled,
        )


class ListDoctorDayAppointments:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: str,
        fecha: str,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        return await self._repo.find_by_doctor_and_date(
            doctor_id=doctor_id,
            fecha=fecha,
            exclude_cancelled=exclude_cancelled,
        )
