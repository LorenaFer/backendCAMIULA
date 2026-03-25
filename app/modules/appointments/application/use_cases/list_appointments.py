from datetime import date
from typing import List, Optional, Tuple
from app.modules.appointments.domain.entities.appointment import Appointment
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository


class ListAppointmentsUseCase:
    """Lista citas con filtros y paginación.

    Complejidad: O(log n + k) donde k = page_size.
    """

    def __init__(self, appointment_repo: AppointmentRepository) -> None:
        self._repo = appointment_repo

    async def execute(
        self,
        page: int,
        page_size: int,
        fecha: Optional[date] = None,
        doctor_id: Optional[str] = None,
        specialty_id: Optional[str] = None,
        estado: Optional[str] = None,
        q: Optional[str] = None,
        mes: Optional[str] = None,
        excluir_canceladas: bool = False,
    ) -> Tuple[List[Appointment], int]:
        return await self._repo.list_filtered(
            page=page,
            page_size=page_size,
            fecha=fecha,
            doctor_id=doctor_id,
            specialty_id=specialty_id,
            estado=estado,
            q=q,
            mes=mes,
            excluir_canceladas=excluir_canceladas,
        )
