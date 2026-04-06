"""Pydantic schemas for the Patient resource."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Input ────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    """Register a new patient (admin/staff)."""

    dni: str = Field(..., max_length=20, description="National ID (unique)", example="V-12345678")
    first_name: str = Field(..., max_length=100, description="First name", example="Juan")
    last_name: str = Field(..., max_length=100, description="Last name", example="Perez Garcia")
    university_relation: str = Field(..., max_length=20, description="Relation with ULA: estudiante, personal, docente, familia, externo", example="estudiante")
    sex: Optional[str] = Field(None, max_length=1, description="Sex: M or F", example="M")
    birth_date: Optional[str] = Field(None, description="Date of birth (ISO YYYY-MM-DD)", example="1998-05-15")
    birth_place: Optional[str] = Field(None, max_length=200, description="Place of birth", example="Merida, Venezuela")
    marital_status: Optional[str] = Field(None, max_length=20, description="Marital status: soltero, casado, divorciado, viudo", example="soltero")
    religion: Optional[str] = Field(None, max_length=100, description="Religion", example="Catolica")
    origin: Optional[str] = Field(None, max_length=200, description="Geographic origin", example="Merida")
    home_address: Optional[str] = Field(None, max_length=300, description="Residential address", example="Av. Universidad, Res. Los Andes, Merida")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number", example="0414-1234567")
    profession: Optional[str] = Field(None, max_length=100, description="Profession/degree", example="Ingeniero")
    current_occupation: Optional[str] = Field(None, max_length=100, description="Current job title", example="Desarrollador")
    work_address: Optional[str] = Field(None, max_length=300, description="Work address", example="Av. Las Americas, Merida")
    economic_classification: Optional[str] = Field(None, max_length=50, description="Socioeconomic class", example="III")
    family_relationship: Optional[str] = Field(None, max_length=20, description="Relationship to holder: hijo, esposa, padre", example="hijo")
    fk_holder_patient_id: Optional[str] = Field(None, max_length=36, description="UUID of the holder patient (for dependents)")
    medical_data: Optional[dict] = Field(None, description="Medical info (JSONB): blood_type, allergies, medical_alerts", example={"blood_type": "O+", "allergies": "Penicilina"})
    emergency_contact: Optional[dict] = Field(None, description="Emergency contact (JSONB)", example={"name": "Maria Perez", "phone": "0414-9876543", "relationship": "Madre"})

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "dni": "V-12345678", "first_name": "Juan", "last_name": "Perez Garcia",
            "university_relation": "estudiante", "sex": "M", "birth_date": "1998-05-15",
            "phone": "0414-1234567", "medical_data": {"blood_type": "O+"},
        }
    })


class PatientRegister(BaseModel):
    """Extended registration from ULA patient portal (public, no auth required)."""

    dni: str = Field(..., max_length=20, description="National ID", example="V-12345678")
    first_name: str = Field(..., max_length=100, description="First name", example="Maria")
    last_name: str = Field(..., max_length=100, description="Last name", example="Garcia")
    university_relation: str = Field(..., max_length=20, description="Relation with ULA", example="estudiante")
    phone: Optional[str] = Field(None, max_length=20, description="Phone", example="0414-1234567")
    email: Optional[str] = Field(None, max_length=200, description="Email", example="maria@ula.ve")
    sex: Optional[str] = Field(None, max_length=1, description="Sex: M or F", example="F")
    birth_date: Optional[str] = Field(None, description="Date of birth (ISO)", example="2000-03-20")
    country: Optional[str] = Field(None, max_length=100, description="Country of birth (composed into birth_place)", example="Venezuela")
    state_geo: Optional[str] = Field(None, max_length=100, description="State (composed into birth_place)", example="Merida")
    city: Optional[str] = Field(None, max_length=100, description="City (composed into birth_place)", example="Merida")
    marital_status: Optional[str] = Field(None, max_length=20, description="Marital status", example="soltero")
    blood_type: Optional[str] = Field(None, max_length=10, description="Blood type (stored in medical_data)", example="A+")
    religion: Optional[str] = Field(None, max_length=100, example="Catolica")
    economic_classification: Optional[str] = Field(None, max_length=50, example="III")
    profession: Optional[str] = Field(None, max_length=100, example="Estudiante")
    current_occupation: Optional[str] = Field(None, max_length=100, example="Estudiante")
    family_relationship: Optional[str] = Field(None, max_length=20, description="Relationship to holder patient", example="hijo")
    holder_dni: Optional[str] = Field(None, max_length=20, description="Dni of the holder patient (resolved to fk_holder_patient_id)", example="V-98765432")
    home_address: Optional[str] = Field(None, max_length=300, example="Av. Universidad, Merida")
    work_address: Optional[str] = Field(None, max_length=300)
    emergency_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name (stored in emergency_contact JSONB)", example="Pedro Garcia")
    emergency_relationship: Optional[str] = Field(None, max_length=50, description="Relationship to emergency contact", example="Padre")
    emergency_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone", example="0274-2401111")
    emergency_address: Optional[str] = Field(None, max_length=300, description="Emergency contact address")
    allergies: Optional[str] = Field(None, max_length=500, description="Known allergies (stored in medical_data)", example="Penicilina, Mariscos")
    medical_alerts: Optional[str] = Field(None, max_length=500, description="Medical alerts (stored in medical_data)", example="Hipertenso")


# ─── Output ───────────────────────────────────────────────────


class PatientResponse(BaseModel):
    """Full patient data including medical and emergency info."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    nhm: int = Field(description="Hospital Medical Number (auto-generated)", example=1234)
    dni: str = Field(description="National ID", example="V-12345678")
    first_name: str = Field(description="First name", example="Juan")
    last_name: str = Field(description="Last name", example="Perez Garcia")
    sex: Optional[str] = Field(None, description="Sex: M or F", example="M")
    birth_date: Optional[str] = Field(None, description="Date of birth (ISO)", example="1998-05-15")
    birth_place: Optional[str] = Field(None, description="Place of birth", example="Merida, Venezuela")
    marital_status: Optional[str] = Field(None, description="Marital status", example="soltero")
    religion: Optional[str] = Field(None, example="Catolica")
    origin: Optional[str] = Field(None, description="Geographic origin", example="Merida")
    home_address: Optional[str] = Field(None, description="Residential address", example="Av. Universidad, Merida")
    phone: Optional[str] = Field(None, description="Phone number", example="0414-1234567")
    profession: Optional[str] = Field(None, example="Ingeniero")
    current_occupation: Optional[str] = Field(None, example="Desarrollador")
    work_address: Optional[str] = Field(None)
    economic_classification: Optional[str] = Field(None, example="III")
    university_relation: str = Field(description="Relation with ULA", example="estudiante")
    family_relationship: Optional[str] = Field(None, description="Relationship to holder", example="hijo")
    fk_holder_patient_id: Optional[str] = Field(None, description="Holder patient UUID")
    medical_data: dict = Field(default={}, description="Medical info JSONB", example={"blood_type": "O+", "allergies": "Penicilina"})
    emergency_contact: Optional[dict] = Field(None, description="Emergency contact JSONB", example={"name": "Maria Perez", "phone": "0414-9876543"})
    is_new: bool = Field(description="True if first-time patient", example=True)
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO)", example="2026-01-15T10:30:00+00:00")


class PatientPublicResponse(BaseModel):
    """Minimal patient data (no sensitive fields). Used for search results and portal."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Patient UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    nhm: int = Field(description="Hospital Medical Number", example=1234)
    first_name: str = Field(description="First name", example="Juan")
    last_name: str = Field(description="Last name", example="Perez Garcia")
    university_relation: str = Field(description="Relation with ULA", example="estudiante")
    is_new: bool = Field(description="First-time patient flag", example=True)


class MaxNhmResponse(BaseModel):
    """Highest NHM currently registered."""

    max_nhm: int = Field(description="Highest Hospital Medical Number in the database", example=1250)
