from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateAppointmentRequest(BaseModel):
    paciente_id: str
    doctor_id: str
    especialidad_id: str
    fecha: date
    hora_inicio: str = Field(pattern=r"^\d{2}:\d{2}$")
    hora_fin: str = Field(pattern=r"^\d{2}:\d{2}$")
    duracion_min: int
    es_primera_vez: bool = False
    motivo_consulta: Optional[str] = None
    observaciones: Optional[str] = None


class ChangeStatusRequest(BaseModel):
    estado: str


class CheckSlotResponse(BaseModel):
    ocupado: bool


class PatientInAppointment(BaseModel):
    id: str
    nhm: int
    nombre: str
    apellido: str
    cedula: str
    relacion_univ: str


class DoctorInAppointment(BaseModel):
    id: str
    nombre: str
    apellido: str
    especialidad: str


class AppointmentResponse(BaseModel):
    id: str
    paciente_id: str
    doctor_id: str
    especialidad_id: str
    fecha: date
    hora_inicio: str
    hora_fin: str
    duracion_min: int
    es_primera_vez: bool
    estado: str
    motivo_consulta: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    paciente: Optional[PatientInAppointment] = None
    doctor: Optional[DoctorInAppointment] = None
