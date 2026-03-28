from __future__ import annotations
from typing import Optional

from app.core.exceptions import AppException
from app.modules.form_schemas.application.dtos.form_schema_dto import UpsertFormSchemaDTO
from app.modules.form_schemas.domain.entities.form_schema import FormSchema
from app.modules.form_schemas.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class UpsertFormSchemaUseCase:
    """Crea o actualiza un schema de formulario. Upsert por specialty_id."""

    def __init__(self, schema_repo: FormSchemaRepository) -> None:
        self._repo = schema_repo

    async def execute(
        self, dto: UpsertFormSchemaDTO, upserted_by: Optional[str] = None
    ) -> FormSchema:
        schema = FormSchema(
            id=dto.schema_id,
            version=dto.version,
            specialty_id=dto.specialty_id,
            specialty_name=dto.specialty_name,
            schema_json=dto.schema_json,
        )
        try:
            schema.validate()
        except ValueError as exc:
            raise AppException(str(exc), status_code=422)

        return await self._repo.upsert(schema, upserted_by=upserted_by)
