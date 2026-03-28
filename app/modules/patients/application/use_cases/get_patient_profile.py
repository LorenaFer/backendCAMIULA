from app.core.exceptions import NotFoundException
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class GetPatientProfileUseCase:
    """Obtiene la ficha completa de un paciente por cédula.

    Complejidad: O(log n) — lookup por índice.
    """

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._repo = patient_repo

    async def execute(self, cedula: str) -> Patient:
        patient = await self._repo.get_by_cedula(cedula)
        if patient is None:
            raise NotFoundException("Paciente no encontrado")
        return patient
