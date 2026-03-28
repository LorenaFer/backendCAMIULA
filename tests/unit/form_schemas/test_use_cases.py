"""TDD — FormSchema use cases tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


def make_schema(id="medicina-general-v1", specialty_id="medicina-general"):
    from app.modules.form_schemas.domain.entities.form_schema import FormSchema
    return FormSchema(
        id=id,
        version="1.0",
        specialty_id=specialty_id,
        specialty_name="Medicina General",
        schema_json={"id": id, "sections": []},
        created_at=datetime(2026, 3, 1),
        updated_at=datetime(2026, 3, 1),
    )


# ──────────────────────────────────────────────────────────────────────────────
# ListFormSchemasUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestListFormSchemasUseCase:
    @pytest.mark.asyncio
    async def test_returns_all_schemas(self):
        from app.modules.form_schemas.application.use_cases.list_form_schemas import (
            ListFormSchemasUseCase,
        )
        repo = MagicMock()
        repo.list_all = AsyncMock(
            return_value=[make_schema("medicina-general-v1"), make_schema("odontologia-v1", "odontologia")]
        )

        uc = ListFormSchemasUseCase(schema_repo=repo)
        result = await uc.execute()

        assert len(result) == 2
        repo.list_all.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# GetFormSchemaUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestGetFormSchemaUseCase:
    @pytest.mark.asyncio
    async def test_returns_schema_by_id(self):
        from app.modules.form_schemas.application.use_cases.get_form_schema import (
            GetFormSchemaUseCase,
        )
        repo = MagicMock()
        repo.get_by_specialty_id_or_key = AsyncMock(return_value=make_schema())

        uc = GetFormSchemaUseCase(schema_repo=repo)
        result = await uc.execute("medicina-general")

        assert result.specialty_id == "medicina-general"

    @pytest.mark.asyncio
    async def test_returns_fallback_when_not_found(self):
        from app.modules.form_schemas.application.use_cases.get_form_schema import (
            GetFormSchemaUseCase,
        )
        repo = MagicMock()
        fallback = make_schema()
        repo.get_by_specialty_id_or_key = AsyncMock(side_effect=[None, fallback])
        repo.get_by_id = AsyncMock(return_value=None)

        uc = GetFormSchemaUseCase(schema_repo=repo)
        result = await uc.execute("unknown-specialty")

        # Should return fallback (medicina-general)
        assert result is not None
        assert result.specialty_id == "medicina-general"


# ──────────────────────────────────────────────────────────────────────────────
# UpsertFormSchemaUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestUpsertFormSchemaUseCase:
    @pytest.mark.asyncio
    async def test_upserts_schema(self):
        from app.modules.form_schemas.application.use_cases.upsert_form_schema import (
            UpsertFormSchemaUseCase,
        )
        from app.modules.form_schemas.application.dtos.form_schema_dto import UpsertFormSchemaDTO

        repo = MagicMock()
        saved = make_schema()
        repo.upsert = AsyncMock(return_value=saved)

        uc = UpsertFormSchemaUseCase(schema_repo=repo)
        dto = UpsertFormSchemaDTO(
            schema_id="medicina-general-v1",
            version="1.0",
            specialty_id="medicina-general",
            specialty_name="Medicina General",
            schema_json={"id": "medicina-general-v1", "sections": []},
        )
        result = await uc.execute(dto, upserted_by="user-1")

        assert result.id == "medicina-general-v1"
        repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_if_schema_json_invalid(self):
        from app.modules.form_schemas.application.use_cases.upsert_form_schema import (
            UpsertFormSchemaUseCase,
        )
        from app.modules.form_schemas.application.dtos.form_schema_dto import UpsertFormSchemaDTO
        from app.core.exceptions import AppException

        repo = MagicMock()

        uc = UpsertFormSchemaUseCase(schema_repo=repo)
        dto = UpsertFormSchemaDTO(
            schema_id="test-v1",
            version="1.0",
            specialty_id="test",
            specialty_name="Test",
            schema_json={"id": "test-v1"},  # missing sections
        )
        with pytest.raises(AppException):
            await uc.execute(dto, upserted_by="user-1")


# ──────────────────────────────────────────────────────────────────────────────
# DeleteFormSchemaUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestDeleteFormSchemaUseCase:
    @pytest.mark.asyncio
    async def test_deletes_schema(self):
        from app.modules.form_schemas.application.use_cases.delete_form_schema import (
            DeleteFormSchemaUseCase,
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=make_schema())
        repo.delete = AsyncMock(return_value=None)

        uc = DeleteFormSchemaUseCase(schema_repo=repo)
        await uc.execute("medicina-general-v1")

        repo.delete.assert_called_once_with("medicina-general-v1", deleted_by=None)

    @pytest.mark.asyncio
    async def test_raises_if_not_found(self):
        from app.modules.form_schemas.application.use_cases.delete_form_schema import (
            DeleteFormSchemaUseCase,
        )
        from app.core.exceptions import AppException

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)

        uc = DeleteFormSchemaUseCase(schema_repo=repo)
        with pytest.raises(AppException):
            await uc.execute("nonexistent-v1")
