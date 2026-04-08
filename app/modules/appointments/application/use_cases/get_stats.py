"""Use case: get appointment stats."""

from typing import Any, Dict, Optional

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class GetAppointmentStats:
    def __init__(self, repo: AppointmentRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        date_str: Optional[str] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._repo.get_stats(
            date_str=date_str,
            doctor_id=doctor_id,
            specialty_id=specialty_id,
            status_filter=status_filter,
        )
