from __future__ import annotations
from datetime import date
from typing import Any, Dict, Optional

from app.modules.appointments.domain.repositories.appointment_repository import (
    AppointmentRepository,
)


class GetAppointmentStatsUseCase:
    """Estadísticas de citas para el dashboard. O(n) scan con filtros."""

    def __init__(self, appointment_repo: AppointmentRepository) -> None:
        self._repo = appointment_repo

    async def execute(
        self,
        fecha: Optional[date] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._repo.get_stats(
            fecha=fecha,
            doctor_id=doctor_id,
            specialty_id=specialty_id,
        )
