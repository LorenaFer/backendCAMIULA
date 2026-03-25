from typing import Optional

from pydantic import BaseModel, Field


class AvailabilityBlockResponse(BaseModel):
    id: str
    doctor_id: str
    day_of_week: int
    hora_inicio: str
    hora_fin: str
    duracion_slot: int


class CreateAvailabilityBlockRequest(BaseModel):
    doctor_id: str
    day_of_week: int = Field(ge=1, le=5)
    hora_inicio: str = Field(pattern=r"^\d{2}:\d{2}$")
    hora_fin: str = Field(pattern=r"^\d{2}:\d{2}$")
    duracion_slot: int = Field(ge=15)


class UpdateAvailabilityBlockRequest(BaseModel):
    hora_inicio: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    hora_fin: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")


class ExceptionCheckResponse(BaseModel):
    excepcion: bool
