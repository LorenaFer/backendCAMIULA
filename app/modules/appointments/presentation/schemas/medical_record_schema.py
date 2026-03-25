from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class UpsertMedicalRecordRequest(BaseModel):
    cita_id: str
    paciente_id: str
    doctor_id: str
    evaluacion: Dict[str, Any]


class MarkPreparedRequest(BaseModel):
    preparado_por: str


class MedicalRecordResponse(BaseModel):
    id: str
    cita_id: str
    paciente_id: str
    doctor_id: str
    evaluacion: Dict[str, Any]
    preparado: bool
    preparado_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
