from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MedicalDataSchema(BaseModel):
    tipo_sangre: Optional[str] = None
    alergias: List[str] = Field(default_factory=list)
    numero_contacto: Optional[str] = None
    condiciones: List[str] = Field(default_factory=list)


class EmergencyContactSchema(BaseModel):
    nombre: Optional[str] = None
    parentesco: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None


class PatientCreateRequest(BaseModel):
    cedula: str = Field(min_length=1, max_length=20)
    first_name: str = Field(alias="nombre", min_length=1, max_length=255)
    last_name: str = Field(alias="apellido", min_length=1, max_length=255)
    university_relation: str = Field(alias="relacion_univ")
    sex: Optional[str] = Field(None, alias="sexo", max_length=1)
    birth_date: Optional[date] = Field(None, alias="fecha_nacimiento")
    birth_place: Optional[str] = Field(None, alias="lugar_nacimiento")
    marital_status: Optional[str] = Field(None, alias="estado_civil")
    religion: Optional[str] = Field(None, alias="religion")
    origin: Optional[str] = Field(None, alias="procedencia")
    home_address: Optional[str] = Field(None, alias="direccion_habitacion")
    phone: Optional[str] = Field(None, alias="telefono")
    profession: Optional[str] = Field(None, alias="profesion")
    current_occupation: Optional[str] = Field(None, alias="ocupacion_actual")
    work_address: Optional[str] = Field(None, alias="direccion_trabajo")
    economic_classification: Optional[str] = Field(
        None, alias="clasificacion_economica"
    )
    family_relationship: Optional[str] = Field(None, alias="parentesco")
    holder_patient_id: Optional[str] = Field(None, alias="titular_nhm")
    medical_data: Optional[MedicalDataSchema] = Field(None, alias="datos_medicos")
    emergency_contact: Optional[EmergencyContactSchema] = Field(
        None, alias="contacto_emergencia"
    )

    model_config = {"populate_by_name": True}


class PatientPublicResponse(BaseModel):
    """Datos reducidos del paciente — para búsquedas públicas."""

    id: str
    nhm: int
    nombre: str
    apellido: str
    relacion_univ: str
    es_nuevo: bool


class PatientFullResponse(BaseModel):
    """Ficha completa del paciente — datos sensibles."""

    id: str
    nhm: int
    cedula: str
    nombre: str
    apellido: str
    sexo: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    lugar_nacimiento: Optional[str] = None
    edad: Optional[int] = None
    estado_civil: Optional[str] = None
    religion: Optional[str] = None
    procedencia: Optional[str] = None
    direccion_habitacion: Optional[str] = None
    telefono: Optional[str] = None
    profesion: Optional[str] = None
    ocupacion_actual: Optional[str] = None
    direccion_trabajo: Optional[str] = None
    clasificacion_economica: Optional[str] = None
    relacion_univ: str
    parentesco: Optional[str] = None
    titular_nhm: Optional[str] = None
    datos_medicos: Optional[Dict[str, Any]] = None
    contacto_emergencia: Optional[Dict[str, Any]] = None
    es_nuevo: bool
    created_at: Optional[datetime] = None


class PatientCreatedResponse(BaseModel):
    """Response tras crear un paciente."""

    id: str
    nhm: int
    cedula: str
    nombre: str
    apellido: str
    relacion_univ: str
    es_nuevo: bool
    created_at: Optional[datetime] = None


class MaxNhmResponse(BaseModel):
    max_nhm: int
