"""Abstract repository interface for Form Schemas."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.medical_records.domain.entities.form_schema import FormSchema


class FormSchemaRepository(ABC):

    @abstractmethod
    async def find_by_specialty(self, specialty_key: str) -> Optional[FormSchema]:
        """Find by specialty UUID or normalized name."""
        ...

    @abstractmethod
    async def find_all(self) -> List[FormSchema]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> FormSchema:
        ...

    @abstractmethod
    async def update(self, schema_id: str, data: dict, updated_by: str) -> FormSchema:
        ...

    @abstractmethod
    async def soft_delete(self, specialty_key: str, deleted_by: str) -> None:
        """Soft delete by specialty normalized name."""
        ...
