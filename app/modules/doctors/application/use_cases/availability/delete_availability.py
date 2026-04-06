"""Use case: Soft-delete availability block."""

from app.core.exceptions import NotFoundException
from app.modules.doctors.domain.repositories.availability_repository import (
    AvailabilityRepository,
)


class DeleteAvailability:

    def __init__(self, repo: AvailabilityRepository) -> None:
        self._repo = repo

    async def execute(
        self, doctor_id: str, block_id: str, deleted_by: str
    ) -> None:
        existing = await self._repo.find_by_id(doctor_id, block_id)
        if not existing:
            raise NotFoundException("Bloque de disponibilidad no encontrado.")
        await self._repo.soft_delete(doctor_id, block_id, deleted_by)
