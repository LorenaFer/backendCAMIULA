"""SQLAlchemy implementation of the Form Schema repository."""

import unicodedata
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.medical_records.domain.entities.form_schema import FormSchema
from app.modules.medical_records.domain.repositories.form_schema_repository import (
    FormSchemaRepository,
)
from app.modules.medical_records.infrastructure.models import FormSchemaModel
from app.shared.database.mixins import RecordStatus


def normalize_specialty_name(name: str) -> str:
    """Normalize specialty name: lowercase, strip accents, replace spaces with hyphens."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_text = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_text.strip().lower().replace(" ", "-")


class SQLAlchemyFormSchemaRepository(FormSchemaRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # ORM -> domain entity
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: FormSchemaModel) -> FormSchema:
        return FormSchema(
            id=model.id,
            specialty_id=model.specialty_id,
            specialty_name=model.specialty_name,
            version=model.version,
            schema_json=model.schema_json,
            status=model.status.value if hasattr(model.status, "value") else model.status,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
            updated_by=model.updated_by,
        )

    # ──────────────────────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────────────────────

    async def find_by_specialty(self, specialty_key: str) -> Optional[FormSchema]:
        """Find by specialty UUID or normalized name."""
        # Try UUID match first
        result = await self._session.execute(
            select(FormSchemaModel).where(
                FormSchemaModel.specialty_id == specialty_key,
                FormSchemaModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)

        # Fall back to normalized name match
        normalized = normalize_specialty_name(specialty_key)
        result = await self._session.execute(
            select(FormSchemaModel).where(
                FormSchemaModel.status == RecordStatus.ACTIVE,
            )
        )
        rows = result.scalars().all()
        for row in rows:
            if normalize_specialty_name(row.specialty_name) == normalized:
                return self._to_entity(row)

        return None

    async def find_by_specialty_id(self, specialty_id: str) -> Optional[FormSchema]:
        """Find active schema by specialty_id only."""
        result = await self._session.execute(
            select(FormSchemaModel).where(
                FormSchemaModel.specialty_id == specialty_id,
                FormSchemaModel.status == RecordStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_all(self) -> List[FormSchema]:
        result = await self._session.execute(
            select(FormSchemaModel)
            .where(FormSchemaModel.status == RecordStatus.ACTIVE)
            .order_by(FormSchemaModel.specialty_name)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ──────────────────────────────────────────────────────────
    # Writes
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> FormSchema:
        model = FormSchemaModel(
            id=str(uuid4()),
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, schema_id: str, data: dict, updated_by: str) -> FormSchema:
        data["updated_by"] = updated_by
        data["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            sql_update(FormSchemaModel)
            .where(FormSchemaModel.id == schema_id)
            .values(**data)
        )
        await self._session.flush()
        # Re-fetch
        result = await self._session.execute(
            select(FormSchemaModel).where(FormSchemaModel.id == schema_id)
        )
        model = result.scalar_one()
        return self._to_entity(model)

    async def soft_delete(self, specialty_key: str, deleted_by: str) -> None:
        """Soft delete by normalized specialty name."""
        normalized = normalize_specialty_name(specialty_key)

        result = await self._session.execute(
            select(FormSchemaModel).where(
                FormSchemaModel.status == RecordStatus.ACTIVE,
            )
        )
        rows = result.scalars().all()
        for row in rows:
            if normalize_specialty_name(row.specialty_name) == normalized:
                await self._session.execute(
                    sql_update(FormSchemaModel)
                    .where(FormSchemaModel.id == row.id)
                    .values(
                        status=RecordStatus.TRASH,
                        deleted_at=datetime.now(timezone.utc),
                        deleted_by=deleted_by,
                    )
                )
                return

        from app.core.exceptions import NotFoundException
        raise NotFoundException("Form schema not found for the given specialty.")
