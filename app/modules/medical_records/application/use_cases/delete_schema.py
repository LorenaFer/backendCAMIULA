"""Use case: Soft delete form schema by specialty normalized name."""

from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class DeleteSchema:

    def __init__(self, repo: FormSchemaRepository) -> None:
        self._repo = repo

    async def execute(self, specialty_key: str, deleted_by: str) -> None:
        await self._repo.soft_delete(specialty_key, deleted_by)
