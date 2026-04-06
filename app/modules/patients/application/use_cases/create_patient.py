"""Use case: create patient (admin/analyst)."""

from app.core.exceptions import ConflictException
from app.modules.patients.application.dtos.patient_dto import CreatePatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)


class CreatePatient:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dto: CreatePatientDTO, created_by: str) -> Patient:
        existing = await self._repo.find_by_dni(dto.dni)
        if existing:
            raise ConflictException(
                f"Ya existe un paciente registrado con la dni '{dto.dni}'."
            )

        nhm = await self._repo.get_next_nhm()

        data = {
            "dni": dto.dni,
            "nhm": nhm,
            "first_name": dto.first_name,
            "last_name": dto.last_name,
            "sex": dto.sex,
            "birth_date": dto.birth_date,
            "birth_place": dto.birth_place,
            "marital_status": dto.marital_status,
            "religion": dto.religion,
            "origin": dto.origin,
            "home_address": dto.home_address,
            "phone": dto.phone,
            "profession": dto.profession,
            "current_occupation": dto.current_occupation,
            "work_address": dto.work_address,
            "economic_classification": dto.economic_classification,
            "university_relation": dto.university_relation,
            "family_relationship": dto.family_relationship,
            "fk_holder_patient_id": dto.fk_holder_patient_id,
            "medical_data": dto.medical_data or {},
            "emergency_contact": dto.emergency_contact,
            "is_new": True,
            "patient_status": "active",
        }
        return await self._repo.create(data, created_by)
