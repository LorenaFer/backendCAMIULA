from datetime import date, time
from app.modules.appointments.domain.repositories.appointment_repository import AppointmentRepository


class CheckSlotAvailabilityUseCase:
    """Verifica si un slot está disponible. O(log n) con índice compuesto."""

    def __init__(self, appointment_repo: AppointmentRepository) -> None:
        self._repo = appointment_repo

    async def execute(
        self, doctor_id: str, appointment_date: date, start_time: time
    ) -> bool:
        """Returns True si el slot está ocupado."""
        from datetime import timedelta, datetime

        # Asumir slot de 30 min para check rápido
        start_dt = datetime.combine(appointment_date, start_time)
        end_dt = start_dt + timedelta(minutes=30)
        end_time = end_dt.time()

        return await self._repo.is_slot_occupied(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
        )
