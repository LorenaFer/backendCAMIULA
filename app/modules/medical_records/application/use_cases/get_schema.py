"""Use case: Get form schema by specialty UUID or normalized name."""

from typing import Optional

from app.modules.medical_records.domain.entities.form_schema import FormSchema
from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)


class GetSchema:

    def __init__(self, repo: FormSchemaRepository) -> None:
        self._repo = repo

    async def execute(self, specialty_key: str) -> Optional[FormSchema]:
        return await self._repo.find_by_specialty(specialty_key)
