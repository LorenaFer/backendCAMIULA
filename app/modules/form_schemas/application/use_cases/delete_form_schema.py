from __future__ import annotations
from typing import Optional

from app.core.exceptions import AppException
from app.modules.form_schemas.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class DeleteFormSchemaUseCase:
    """Soft-delete de un schema de formulario. O(log n) por PK."""

    def __init__(self, schema_repo: FormSchemaRepository) -> None:
        self._repo = schema_repo

    async def execute(
        self, schema_id: str, deleted_by: Optional[str] = None
    ) -> None:
        schema = await self._repo.get_by_id(schema_id)
        if schema is None:
            raise AppException(
                f"Schema '{schema_id}' no encontrado", status_code=404
            )
        await self._repo.delete(schema_id, deleted_by=deleted_by)
