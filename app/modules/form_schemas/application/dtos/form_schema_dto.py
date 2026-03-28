from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class UpsertFormSchemaDTO:
    schema_id: str
    version: str
    specialty_id: str
    specialty_name: str
    schema_json: Dict[str, Any]
