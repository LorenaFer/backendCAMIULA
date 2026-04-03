"""DTOs for the patients module."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreatePatientDTO:
    cedula: str
    first_name: str
    last_name: str
    university_relation: str
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    marital_status: Optional[str] = None
    religion: Optional[str] = None
    origin: Optional[str] = None
    home_address: Optional[str] = None
    phone: Optional[str] = None
    profession: Optional[str] = None
    current_occupation: Optional[str] = None
    work_address: Optional[str] = None
    economic_classification: Optional[str] = None
    family_relationship: Optional[str] = None
    fk_holder_patient_id: Optional[str] = None
    medical_data: Optional[dict] = None
    emergency_contact: Optional[dict] = None


@dataclass
class RegisterPatientDTO(CreatePatientDTO):
    """Extended DTO for ULA portal registration.

    Extra fields composed by the backend:
    - country, state_geo, city -> birth_place
    - emergency_* -> emergency_contact
    - allergies, medical_alerts -> medical_data
    - holder_cedula -> fk_holder_patient_id (lookup)
    """

    country: Optional[str] = None
    state_geo: Optional[str] = None
    city: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_name: Optional[str] = None
    emergency_relationship: Optional[str] = None
    emergency_phone: Optional[str] = None
    emergency_address: Optional[str] = None
    allergies: Optional[str] = None
    medical_alerts: Optional[str] = None
    holder_cedula: Optional[str] = None
    email: Optional[str] = None
