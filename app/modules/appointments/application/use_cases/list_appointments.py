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
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        q: Optional[str] = None,
        fk_patient_id: Optional[str] = None,
    ) -> Tuple[List[Appointment], int]:
        return await self._repo.find_all(
            page=page,
            page_size=page_size,
            date_str=date_str,
            doctor_id=doctor_id,
            specialty_id=specialty_id,
            status_filter=status_filter,
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
        date_str: str,
        exclude_cancelled: bool = True,
    ) -> List[Appointment]:
        return await self._repo.find_by_doctor_and_date(
            doctor_id=doctor_id,
            date_str=date_str,
            exclude_cancelled=exclude_cancelled,
        )
