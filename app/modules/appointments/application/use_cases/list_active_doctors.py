from typing import List
from app.modules.appointments.domain.entities.doctor import Doctor
from app.modules.appointments.domain.repositories.doctor_repository import DoctorRepository


class ListActiveDoctorsUseCase:
    """Lista doctores activos. O(log n + k) con paginación implícita."""

    def __init__(self, doctor_repo: DoctorRepository) -> None:
        self._repo = doctor_repo

    async def execute(self) -> List[Doctor]:
        return await self._repo.list_active()
