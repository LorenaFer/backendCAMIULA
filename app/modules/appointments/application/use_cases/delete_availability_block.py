from app.core.exceptions import NotFoundException
from app.modules.appointments.domain.repositories.availability_repository import AvailabilityRepository


class DeleteAvailabilityBlockUseCase:
    def __init__(self, availability_repo: AvailabilityRepository) -> None:
        self._repo = availability_repo

    async def execute(self, block_id: str, deleted_by: str) -> None:
        block = await self._repo.get_block_by_id(block_id)
        if block is None:
            raise NotFoundException("Bloque de disponibilidad no encontrado")
        await self._repo.delete_block(block_id, deleted_by)
