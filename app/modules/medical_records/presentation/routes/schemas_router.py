"""FastAPI routes for Form Schemas."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.medical_records.application.dtos.medical_record_dto import (
    UpsertFormSchemaDTO,
)
from app.modules.medical_records.application.use_cases.delete_schema import DeleteSchema
from app.modules.medical_records.application.use_cases.get_schema import GetSchema
from app.modules.medical_records.application.use_cases.list_schemas import ListSchemas
from app.modules.medical_records.application.use_cases.upsert_schema import UpsertSchema
from app.modules.medical_records.infrastructure.repositories.sqlalchemy_form_schema_repository import (
    SQLAlchemyFormSchemaRepository,
)
from app.modules.medical_records.presentation.schemas.form_schema_schemas import (
    FormSchemaResponse,
    FormSchemaUpsert,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/schemas", tags=["Medical Records — Form Schemas"])


@router.get("", summary="List all form schemas")
async def list_schemas(
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyFormSchemaRepository(session)
    schemas = await ListSchemas(repo).execute()
    data = [FormSchemaResponse(**s.__dict__) for s in schemas]
    return ok(data=data, message="Form schemas retrieved successfully")


@router.get("/{specialty_key}", summary="Get form schema by specialty UUID or name")
async def get_schema(
    specialty_key: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyFormSchemaRepository(session)
    schema = await GetSchema(repo).execute(specialty_key)
    if not schema:
        raise NotFoundException("Form schema not found for this specialty.")
    return ok(
        data=FormSchemaResponse(**schema.__dict__),
        message="Form schema retrieved successfully",
    )


@router.put("", summary="Upsert form schema")
async def upsert_schema(
    body: FormSchemaUpsert,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyFormSchemaRepository(session)
    dto = UpsertFormSchemaDTO(**body.model_dump())
    schema, was_created = await UpsertSchema(repo).execute(dto, user_id)
    response = FormSchemaResponse(**schema.__dict__)
    if was_created:
        return created(data=response, message="Form schema created successfully")
    return ok(data=response, message="Form schema updated successfully")


@router.delete("/{specialty_key}", summary="Soft delete form schema by specialty name")
async def delete_schema(
    specialty_key: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyFormSchemaRepository(session)
    await DeleteSchema(repo).execute(specialty_key, deleted_by=user_id)
    return ok(message="Form schema deleted successfully")
