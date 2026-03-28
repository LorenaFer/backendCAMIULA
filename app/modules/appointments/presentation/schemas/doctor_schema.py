from typing import List, Optional

from pydantic import BaseModel


class SpecialtyResponse(BaseModel):
    id: str
    nombre: str
    activo: bool = True


class SpecialtyCreateRequest(BaseModel):
    nombre: str


class SpecialtyUpdateRequest(BaseModel):
    nombre: str


class DoctorResponse(BaseModel):
    id: str
    nombre: str
    apellido: str
    especialidad_id: str
    activo: bool
    especialidad: Optional[SpecialtyResponse] = None


class DoctorOptionResponse(BaseModel):
    id: str
    nombre_completo: str
    especialidad: str
    especialidad_id: str
    dias_trabajo: List[int]
