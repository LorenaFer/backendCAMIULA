from app.core.exceptions import AppException, ConflictException
from app.modules.patients.application.dtos.patient_dto import CreatePatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository


class CreatePatientUseCase:
    """Registra un nuevo paciente. Asigna NHM automáticamente.

    Validaciones:
    - Cédula única (O(log n) con índice)
    - Si tercero: parentesco y titular obligatorios, titular debe existir
    - NHM: atómico via secuencia PostgreSQL

    Complejidad: O(log n)
    """

    def __init__(self, patient_repo: PatientRepository) -> None:
        self._repo = patient_repo

    async def execute(self, dto: CreatePatientDTO, created_by: str) -> Patient:
        # Verificar cédula única
        if await self._repo.exists_by_cedula(dto.cedula):
            raise ConflictException("Ya existe un paciente con esta cédula")

        patient = Patient(
            first_name=dto.first_name,
            last_name=dto.last_name,
            cedula=dto.cedula,
            university_relation=dto.university_relation,
            sex=dto.sex,
            birth_date=dto.birth_date,
            birth_place=dto.birth_place,
            marital_status=dto.marital_status,
            religion=dto.religion,
            origin=dto.origin,
            home_address=dto.home_address,
            phone=dto.phone,
            profession=dto.profession,
            current_occupation=dto.current_occupation,
            work_address=dto.work_address,
            economic_classification=dto.economic_classification,
            family_relationship=dto.family_relationship,
            holder_patient_id=dto.holder_patient_id,
            medical_data=dto.medical_data,
            emergency_contact=dto.emergency_contact,
        )

        # Validar relación universidad
        if patient.university_relation not in Patient.VALID_RELATIONS:
            raise AppException(
                f"Relación universitaria inválida: {patient.university_relation}",
                status_code=422,
            )

        # Validar tercero (parentesco + titular)
        patient.validate_tercero()

        # Si es tercero, verificar que el titular existe
        if patient.university_relation == "tercero":
            holder = await self._repo.get_by_id(patient.holder_patient_id)
            if holder is None:
                raise AppException(
                    "El titular especificado no existe", status_code=422
                )

        # Asignar NHM atómicamente
        patient.nhm = await self._repo.next_nhm()

        return await self._repo.create(patient)
