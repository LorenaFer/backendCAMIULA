from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class GetMaxNhmUseCase:
    """Obtiene el último NHM asignado.

    Complejidad: O(log n) — MAX sobre índice.
    """

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._repo = patient_repo

    async def execute(self) -> int:
        return await self._repo.get_max_nhm()
