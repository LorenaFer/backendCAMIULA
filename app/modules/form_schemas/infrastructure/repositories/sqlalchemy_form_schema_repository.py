from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.form_schemas.domain.entities.form_schema import FormSchema
from app.modules.form_schemas.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)
from app.modules.form_schemas.infrastructure.models import FormSchemaModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyFormSchemaRepository(FormSchemaRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: FormSchemaModel) -> FormSchema:
        return FormSchema(
            id=model.id,
            version=model.version,
            specialty_id=model.specialty_id,
            specialty_name=model.specialty_name,
            schema_json=model.schema_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_all(self) -> List[FormSchema]:
        """Lista todos los schemas activos (excluye soft-deleted)."""
        stmt = (
            select(FormSchemaModel)
            .where(FormSchemaModel.status != RecordStatus.TRASH)
            .order_by(FormSchemaModel.specialty_id)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def get_by_id(self, schema_id: str) -> Optional[FormSchema]:
        stmt = (
            select(FormSchemaModel)
            .where(
                FormSchemaModel.id == schema_id,
                FormSchemaModel.status != RecordStatus.TRASH,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_specialty_id_or_key(self, key: str) -> Optional[FormSchema]:
        """Busca por specialty_id exacto, retorna el más reciente no eliminado."""
        normalized = FormSchema.normalize_name(key)
        stmt = (
            select(FormSchemaModel)
            .where(
                FormSchemaModel.specialty_id == normalized,
                FormSchemaModel.status != RecordStatus.TRASH,
            )
            .order_by(FormSchemaModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def upsert(
        self, schema: FormSchema, upserted_by: Optional[str] = None
    ) -> FormSchema:
        """Upsert por id (PK semántico). O(log n).

        - Creación: llena created_by.
        - Actualización: llena updated_at y updated_by.
        """
        stmt = (
            select(FormSchemaModel)
            .where(FormSchemaModel.id == schema.id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = FormSchemaModel(
                id=schema.id,
                version=schema.version,
                specialty_id=schema.specialty_id,
                specialty_name=schema.specialty_name,
                schema_json=schema.schema_json,
                created_by=upserted_by,
                updated_at=datetime.now(timezone.utc),
                updated_by=upserted_by,
            )
            self._session.add(model)
        else:
            model.version = schema.version
            model.specialty_id = schema.specialty_id
            model.specialty_name = schema.specialty_name
            model.schema_json = schema.schema_json
            model.updated_at = datetime.now(timezone.utc)
            model.updated_by = upserted_by
            # Restaurar registro si estaba eliminado (soft-delete)
            model.status = RecordStatus.ACTIVE
            model.deleted_at = None
            model.deleted_by = None

        await self._session.flush()
        return self._to_entity(model)

    async def delete(
        self, schema_id: str, deleted_by: Optional[str] = None
    ) -> None:
        """Soft-delete: status → T, registra deleted_at y deleted_by."""
        stmt = (
            select(FormSchemaModel)
            .where(
                FormSchemaModel.id == schema_id,
                FormSchemaModel.status != RecordStatus.TRASH,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = RecordStatus.TRASH
            model.deleted_at = datetime.now(timezone.utc)
            model.deleted_by = deleted_by
            await self._session.flush()
