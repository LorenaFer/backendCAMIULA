from __future__ import annotations
from typing import List

from app.modules.form_schemas.domain.entities.form_schema import FormSchema
from app.modules.form_schemas.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class ListFormSchemasUseCase:
    """Lista todos los schemas de formularios disponibles. O(n)."""

    def __init__(self, schema_repo: FormSchemaRepository) -> None:
        self._repo = schema_repo

    async def execute(self) -> List[FormSchema]:
        return await self._repo.list_all()
