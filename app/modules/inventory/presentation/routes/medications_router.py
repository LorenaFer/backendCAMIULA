"""Rutas FastAPI para el recurso Medicamento."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.inventory.application.dtos.medication_dto import (
    CreateMedicationDTO,
    UpdateMedicationDTO,
)
from app.modules.inventory.application.use_cases.medications.create_medication import (
    CreateMedication,
)
from app.modules.inventory.application.use_cases.medications.get_medication_by_id import (
    GetMedicationById,
)
from app.modules.inventory.application.use_cases.medications.get_medications import (
    GetMedications,
)
from app.modules.inventory.application.use_cases.medications.soft_delete_medication import (
    SoftDeleteMedication,
)
from app.modules.inventory.application.use_cases.medications.update_medication import (
    UpdateMedication,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.modules.inventory.presentation.schemas.medication_schemas import (
    MedicationCreate,
    MedicationOptionResponse,
    MedicationResponse,
    MedicationUpdate,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/medications", tags=["Inventory — Medications"])


@router.get("", summary="Listar medicamentos")
async def list_medications(
    search: Optional[str] = Query(None, description="Búsqueda por nombre genérico"),
    status: Optional[str] = Query(None, description="Filtrar por medication_status"),
    therapeutic_class: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    items, total = await GetMedications(repo).execute(
        search=search,
        status=status,
        therapeutic_class=therapeutic_class,
        page=page,
        page_size=page_size,
    )
    data = [MedicationResponse(**m.__dict__) for m in items]
    return paginated(data, total, page, page_size, "Medicamentos obtenidos exitosamente")


@router.get("/options", summary="Lista simplificada para selects")
async def get_medication_options(
    search: Optional[str] = Query(None, description="Filtrar por nombre genérico"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de resultados"),
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    options = await repo.find_options(search=search, limit=limit)
    data = [MedicationOptionResponse(**m.__dict__) for m in options]
    return ok(data=data, message="Opciones de medicamentos obtenidas")


@router.get("/{id}", summary="Detalle de medicamento con stock actual")
async def get_medication(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_optional_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    medication = await GetMedicationById(repo).execute(id)
    if not medication:
        raise NotFoundException("Medicamento no encontrado.")
    return ok(
        data=MedicationResponse(**medication.__dict__),
        message="Medicamento obtenido exitosamente",
    )


@router.post("", summary="Registrar nuevo medicamento", status_code=201)
async def create_medication(
    body: MedicationCreate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    dto = CreateMedicationDTO(**body.model_dump())
    medication = await CreateMedication(repo).execute(dto, created_by=user_id)
    return created(
        data=MedicationResponse(**medication.__dict__),
        message="Medicamento registrado exitosamente",
    )


@router.patch("/{id}", summary="Actualizar medicamento")
async def update_medication(
    id: str,
    body: MedicationUpdate,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    dto = UpdateMedicationDTO(**body.model_dump(exclude_none=True))
    medication = await UpdateMedication(repo).execute(id, dto, updated_by=user_id)
    return ok(
        data=MedicationResponse(**medication.__dict__),
        message="Medicamento actualizado exitosamente",
    )


@router.delete("/{id}", summary="Eliminar medicamento (soft-delete)")
async def delete_medication(
    id: str,
    session: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    repo = SQLAlchemyMedicationRepository(session)
    await SoftDeleteMedication(repo).execute(id, deleted_by=user_id)
    return ok(message="Medicamento eliminado exitosamente")
