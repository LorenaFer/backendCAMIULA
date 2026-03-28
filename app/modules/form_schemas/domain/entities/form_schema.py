"""Entidad de dominio: FormSchema.

Un FormSchema almacena la estructura del formulario médico dinámico
para una especialidad. El backend solo almacena y sirve el JSON;
el renderizado ocurre en el frontend.
"""
from __future__ import annotations

import unicodedata
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class FormSchema:
    id: str                     # e.g. "medicina-general-v1" (PK semántico)
    version: str                # e.g. "1.0"
    specialty_id: str           # key normalizado: "medicina-general"
    specialty_name: str         # nombre legible: "Medicina General"
    schema_json: Dict[str, Any] # estructura completa del formulario
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de dominio
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normaliza un nombre de especialidad a key URL-safe.

        Ejemplo: "Cirugía General" → "cirugia-general"
        """
        # NFD decomposition para separar acentos
        nfd = unicodedata.normalize("NFD", name)
        # Eliminar combining marks (acentos, etc.)
        without_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
        # Minúsculas
        lowered = without_accents.lower()
        # Espacios → guiones
        hyphenated = re.sub(r"\s+", "-", lowered.strip())
        # Solo alfanumérico y guiones
        clean = re.sub(r"[^a-z0-9-]", "", hyphenated)
        return clean

    def validate(self) -> None:
        """Valida estructura básica del schema_json."""
        if "sections" not in self.schema_json:
            raise ValueError(
                "schema_json debe contener el campo 'sections' (array de secciones)"
            )
        if not isinstance(self.schema_json["sections"], list):
            raise ValueError("'sections' debe ser un array")
