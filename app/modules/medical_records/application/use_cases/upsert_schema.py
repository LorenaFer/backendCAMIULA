"""Use case: Upsert form schema (create or update by specialty_id)."""

from app.modules.medical_records.application.dtos.medical_record_dto import (
    UpsertFormSchemaDTO,
)
from app.modules.medical_records.domain.entities.form_schema import FormSchema
from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class UpsertSchema:

    def __init__(self, repo: FormSchemaRepository) -> None:
        self._repo = repo

    async def execute(self, dto: UpsertFormSchemaDTO, user_id: str) -> tuple:
        """Returns (entity, was_created: bool)."""
        existing = await self._repo.find_by_specialty_id(dto.specialty_id)

        data = {
            "specialty_id": dto.specialty_id,
            "specialty_name": dto.specialty_name,
            "version": dto.version,
            "schema_json": dto.schema_json,
        }

        if existing:
            update_data = {k: v for k, v in data.items() if k != "specialty_id"}
            record = await self._repo.update(existing.id, update_data, updated_by=user_id)
            return record, False
        else:
            record = await self._repo.create(data, created_by=user_id)
            return record, True
