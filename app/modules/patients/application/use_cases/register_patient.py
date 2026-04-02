"""Use case: register patient from ULA portal (full form)."""

from datetime import date

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.patients.application.dtos.patient_dto import RegisterPatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import (
    PatientRepository,
)

# University relation codes that indicate a family member
_FAMILY_CODES = {"R", "S", "T", "C", "F"}


class RegisterPatient:
    def __init__(self, repo: PatientRepository) -> None:
        self._repo = repo

    async def execute(self, dto: RegisterPatientDTO, created_by: str) -> Patient:
        existing = await self._repo.find_by_cedula(dto.cedula)
        if existing:
            raise ConflictException(
                f"Ya existe un paciente registrado con la cedula '{dto.cedula}'."
            )

        # If family member, validate holder exists
        holder_id = dto.fk_holder_patient_id
        if dto.university_relation in _FAMILY_CODES:
            if not dto.holder_cedula:
                raise NotFoundException(
                    "Se requiere la cedula del titular para familiares."
                )
            holder = await self._repo.find_by_cedula(dto.holder_cedula)
            if not holder:
                raise NotFoundException(
                    f"Titular con cedula '{dto.holder_cedula}' no encontrado."
                )
            holder_id = holder.id

        # Calculate age from birth_date
        age = dto.age
        if dto.birth_date and not age:
            try:
                born = date.fromisoformat(dto.birth_date)
                today = date.today()
                age = (
                    today.year
                    - born.year
                    - ((today.month, today.day) < (born.month, born.day))
                )
            except ValueError:
                pass

        # Compose birth_place
        birth_place = dto.birth_place
        if not birth_place and any([dto.city, dto.state_geo, dto.country]):
            parts = [p for p in [dto.city, dto.state_geo, dto.country] if p]
            birth_place = ", ".join(parts)

        # Compose medical_data
        medical_data: dict = dto.medical_data or {}
        if dto.blood_type:
            medical_data["blood_type"] = dto.blood_type
        if dto.allergies:
            medical_data["allergies"] = [
                a.strip() for a in dto.allergies.split(",") if a.strip()
            ]
        if dto.medical_alerts:
            medical_data["conditions"] = [
                c.strip() for c in dto.medical_alerts.split(",") if c.strip()
            ]
        if dto.phone:
            medical_data["contact_number"] = dto.phone

        # Compose emergency_contact
        contact = dto.emergency_contact
        if not contact and any(
            [
                dto.emergency_name,
                dto.emergency_relationship,
                dto.emergency_phone,
                dto.emergency_address,
            ]
        ):
            contact = {
                "name": dto.emergency_name,
                "relationship": dto.emergency_relationship,
                "phone": dto.emergency_phone,
                "address": dto.emergency_address,
            }

        nhm = await self._repo.get_next_nhm()

        data = {
            "cedula": dto.cedula,
            "nhm": nhm,
            "first_name": dto.first_name,
            "last_name": dto.last_name,
            "sex": dto.sex,
            "birth_date": dto.birth_date,
            "birth_place": birth_place,
            "age": age,
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
            "fk_holder_patient_id": holder_id,
            "medical_data": medical_data,
            "emergency_contact": contact,
            "is_new": True,
            "patient_status": "active",
        }
        return await self._repo.create(data, created_by)
