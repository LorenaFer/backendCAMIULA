from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UpsertMedicalRecordRequest(BaseModel):
    cita_id: str
    paciente_id: str
    doctor_id: str
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None
    evaluacion: Dict[str, Any]


class MarkPreparedRequest(BaseModel):
    preparado_por: str


class MedicalRecordResponse(BaseModel):
    id: str
    cita_id: str
    paciente_id: str
    doctor_id: str
    schema_id: Optional[str] = None
    schema_version: Optional[str] = None
    evaluacion: Dict[str, Any]
    preparado: bool
    preparado_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PatientHistoryEntry(BaseModel):
    id: str
    cita_id: str
    doctor_id: str
    schema_id: Optional[str] = None
    evaluacion: Dict[str, Any]
    preparado: bool
    created_at: Optional[datetime] = None
