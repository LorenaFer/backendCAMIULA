"""Use case: List all form schemas."""

from typing import List

from app.modules.medical_records.domain.entities.form_schema import FormSchema
from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class ListSchemas:

    def __init__(self, repo: FormSchemaRepository) -> None:
        self._repo = repo

    async def execute(self) -> List[FormSchema]:
        return await self._repo.find_all()
