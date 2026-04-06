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
        fecha: Optional[str] = None,
        doctor_id: Optional[str] = None,
        especialidad_id: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._repo.get_stats(
            fecha=fecha,
            doctor_id=doctor_id,
            especialidad_id=especialidad_id,
            estado=estado,
        )
