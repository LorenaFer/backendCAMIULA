"""Entidades de dominio del módulo de pacientes."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4


@dataclass
class Patient:
    cedula: str
    nombre: str
    apellido: str
    nhm: int
    id: str = field(default_factory=lambda: str(uuid4()))
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
    relacion_univ: str = "tercero"
    parentesco: Optional[str] = None
    titular_nhm: Optional[int] = None
    datos_medicos: dict = field(default_factory=dict)
    contacto_emergencia: dict = field(default_factory=dict)
    es_nuevo: bool = True
    created_at: Optional[str] = None


@dataclass
class PatientHistoryEntry:
    id: str
    fecha: str
    especialidad: Optional[str]
    doctor_nombre: Optional[str]
    diagnostico_descripcion: Optional[str]
    diagnostico_cie10: Optional[str]
