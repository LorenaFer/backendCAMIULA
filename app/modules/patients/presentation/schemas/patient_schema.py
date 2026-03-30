"""Schemas Pydantic del módulo de pacientes."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatosMedicosSchema(BaseModel):
    tipo_sangre: Optional[str] = None
    alergias: list[str] = Field(default_factory=list)
    numero_contacto: Optional[str] = None
    condiciones: list[str] = Field(default_factory=list)


class ContactoEmergenciaSchema(BaseModel):
    nombre: Optional[str] = None
    parentesco: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None


class PatientCreateRequest(BaseModel):
    cedula: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=120)
    apellido: str = Field(..., min_length=1, max_length=120)
    sexo: Optional[Literal["M", "F"]] = None
    fecha_nacimiento: Optional[date] = None
    lugar_nacimiento: Optional[str] = Field(None, max_length=120)
    edad: Optional[int] = Field(None, ge=0, le=130)
    estado_civil: Optional[
        Literal["soltero", "casado", "divorciado", "viudo", "union_libre"]
    ] = None
    religion: Optional[str] = Field(None, max_length=120)
    procedencia: Optional[str] = Field(None, max_length=120)
    direccion_habitacion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=30)
    profesion: Optional[str] = Field(None, max_length=120)
    ocupacion_actual: Optional[str] = Field(None, max_length=120)
    direccion_trabajo: Optional[str] = Field(None, max_length=255)
    clasificacion_economica: Optional[str] = Field(None, max_length=20)
    relacion_univ: Optional[str] = Field(None, max_length=20)
    parentesco: Optional[Literal["hijo", "padre", "madre", "conyuge", "otro"]] = None
    titular_nhm: Optional[int] = Field(None, ge=1)
    datos_medicos: Optional[DatosMedicosSchema] = None
    contacto_emergencia: Optional[ContactoEmergenciaSchema] = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nhm: int
    cedula: str
    nombre: str
    apellido: str
    sexo: Optional[str]
    fecha_nacimiento: Optional[date]
    lugar_nacimiento: Optional[str]
    edad: Optional[int]
    estado_civil: Optional[str]
    religion: Optional[str]
    procedencia: Optional[str]
    direccion_habitacion: Optional[str]
    telefono: Optional[str]
    profesion: Optional[str]
    ocupacion_actual: Optional[str]
    direccion_trabajo: Optional[str]
    clasificacion_economica: Optional[str]
    relacion_univ: str
    parentesco: Optional[str]
    titular_nhm: Optional[int]
    datos_medicos: dict
    contacto_emergencia: dict
    es_nuevo: bool
    created_at: Optional[str]


class PatientHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fecha: str
    especialidad: Optional[str]
    doctor_nombre: Optional[str]
    diagnostico_descripcion: Optional[str]
    diagnostico_cie10: Optional[str]
