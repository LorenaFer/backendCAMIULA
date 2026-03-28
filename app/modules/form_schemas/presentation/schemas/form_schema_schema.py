from typing import Any, List

from pydantic import BaseModel


class UpsertFormSchemaRequest(BaseModel):
    """Body para PUT /api/schemas.

    Acepta la estructura MedicalFormSchema del frontend.
    """
    id: str
    version: str
    specialtyId: str
    specialtyName: str
    sections: List[Any]
