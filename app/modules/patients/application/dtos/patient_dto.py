"""DTOs de casos de uso para pacientes."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class SearchPatientDTO:
    cedula: Optional[str] = None
    nhm: Optional[int] = None


@dataclass
class GetPatientHistoryDTO:
    patient_id: str
    limit: int = 5
    exclude_appointment_id: Optional[str] = None


@dataclass
class CreatePatientDTO:
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
    relacion_univ: Optional[str] = None
    parentesco: Optional[str] = None
    titular_nhm: Optional[int] = None
    datos_medicos: Optional[dict] = field(default_factory=dict)
    contacto_emergencia: Optional[dict] = field(default_factory=dict)
