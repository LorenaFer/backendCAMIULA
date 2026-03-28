from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.form_schemas.domain.entities.form_schema import FormSchema


class FormSchemaRepository(ABC):
    @abstractmethod
    async def list_all(self) -> List[FormSchema]:
        """Lista todos los schemas no eliminados (status != T)."""
        ...

    @abstractmethod
    async def get_by_id(self, schema_id: str) -> Optional[FormSchema]:
        """Obtiene un schema por su ID exacto (ej: 'medicina-general-v1').

        Retorna None si no existe o fue eliminado (status=T).
        """
        ...

    @abstractmethod
    async def get_by_specialty_id_or_key(self, key: str) -> Optional[FormSchema]:
        """Busca schema por specialty_id normalizado o nombre normalizado.

        Retorna el schema más reciente para esa especialidad (status != T).
        """
        ...

    @abstractmethod
    async def upsert(
        self, schema: FormSchema, upserted_by: Optional[str] = None
    ) -> FormSchema:
        """Crea o actualiza un schema. Upsert por id (PK semántico).

        Llena created_by en creación y updated_by en actualización.
        """
        ...

    @abstractmethod
    async def delete(
        self, schema_id: str, deleted_by: Optional[str] = None
    ) -> None:
        """Soft-delete: cambia status a T y registra deleted_at/deleted_by."""
        ...
