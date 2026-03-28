from __future__ import annotations
from typing import Optional

from app.modules.form_schemas.domain.entities.form_schema import FormSchema
from app.modules.form_schemas.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)

_FALLBACK_SPECIALTY_ID = "medicina-general"


class GetFormSchemaUseCase:
    """Obtiene schema por specialty_id/key normalizado.

    Fallback: si no existe, retorna el de Medicina General.
    O(log n) índice en specialty_id.
    """

    def __init__(self, schema_repo: FormSchemaRepository) -> None:
        self._repo = schema_repo

    async def execute(self, key: str) -> Optional[FormSchema]:
        # Normalizar el key por si viene como nombre legible
        normalized = FormSchema.normalize_name(key)
        schema = await self._repo.get_by_specialty_id_or_key(normalized)

        if schema is not None:
            return schema

        # Intentar por ID exacto (el key puede ser el id semántico del schema)
        schema = await self._repo.get_by_id(normalized)
        if schema is not None:
            return schema

        # Fallback: retornar Medicina General
        if normalized != _FALLBACK_SPECIALTY_ID:
            return await self._repo.get_by_specialty_id_or_key(_FALLBACK_SPECIALTY_ID)

        return None
