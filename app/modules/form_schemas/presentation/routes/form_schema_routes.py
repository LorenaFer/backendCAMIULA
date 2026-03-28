from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.form_schemas.application.dtos.form_schema_dto import UpsertFormSchemaDTO
from app.modules.form_schemas.application.use_cases.delete_form_schema import (
    DeleteFormSchemaUseCase,
)
from app.modules.form_schemas.application.use_cases.get_form_schema import (
    GetFormSchemaUseCase,
)
from app.modules.form_schemas.application.use_cases.list_form_schemas import (
    ListFormSchemasUseCase,
)
from app.modules.form_schemas.application.use_cases.upsert_form_schema import (
    UpsertFormSchemaUseCase,
)
from app.modules.form_schemas.domain.entities.form_schema import FormSchema
from app.modules.form_schemas.infrastructure.repositories.sqlalchemy_form_schema_repository import (
    SQLAlchemyFormSchemaRepository,
)
from app.modules.form_schemas.presentation.schemas.form_schema_schema import (
    UpsertFormSchemaRequest,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/schemas", tags=["Form Schemas"])


def _to_response(s: FormSchema) -> dict:
    """Retorna el schema_json (estructura MedicalFormSchema) con timestamps."""
    result = dict(s.schema_json)
    result["created_at"] = s.created_at.isoformat() if s.created_at else None
    result["updated_at"] = s.updated_at.isoformat() if s.updated_at else None
    return result


@router.get("")
async def list_schemas(
    _=Depends(require_permission("schemas:read")),
    db: AsyncSession = Depends(get_db),
):
    """Listar todos los schemas de formularios disponibles."""
    repo = SQLAlchemyFormSchemaRepository(db)
    use_case = ListFormSchemasUseCase(schema_repo=repo)
    schemas = await use_case.execute()
    return ok(data=[_to_response(s) for s in schemas], message="Listado de schemas")


@router.get("/{specialty_key}")
async def get_schema(
    specialty_key: str,
    _=Depends(require_permission("schemas:read")),
    db: AsyncSession = Depends(get_db),
):
    """Obtener schema por ID de especialidad o nombre normalizado.

    Fallback: si no existe, retorna el de Medicina General.
    """
    repo = SQLAlchemyFormSchemaRepository(db)
    use_case = GetFormSchemaUseCase(schema_repo=repo)
    schema = await use_case.execute(specialty_key)
    if schema is None:
        return ok(data=None, message="Schema no encontrado")
    return ok(data=_to_response(schema), message="Schema encontrado")


@router.put("")
async def upsert_schema(
    body: UpsertFormSchemaRequest,
    user=Depends(require_permission("schemas:write")),
    db: AsyncSession = Depends(get_db),
):
    """Crear o actualizar un schema de formulario (upsert por id)."""
    repo = SQLAlchemyFormSchemaRepository(db)
    use_case = UpsertFormSchemaUseCase(schema_repo=repo)

    # Normalizar el specialty_id desde el nombre
    specialty_id = FormSchema.normalize_name(body.specialtyId)

    dto = UpsertFormSchemaDTO(
        schema_id=body.id,
        version=body.version,
        specialty_id=specialty_id,
        specialty_name=body.specialtyName,
        schema_json={
            "id": body.id,
            "version": body.version,
            "specialtyId": specialty_id,
            "specialtyName": body.specialtyName,
            "sections": body.sections,
        },
    )
    schema = await use_case.execute(dto, upserted_by=user.id)
    return ok(data=_to_response(schema), message="Schema guardado")


@router.delete("/{schema_key}", status_code=200)
async def delete_schema(
    schema_key: str,
    user=Depends(require_permission("schemas:write")),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar schema de una especialidad."""
    repo = SQLAlchemyFormSchemaRepository(db)
    use_case = DeleteFormSchemaUseCase(schema_repo=repo)
    await use_case.execute(schema_key, deleted_by=user.id)
    return ok(message="Schema eliminado")
