"""Implementación SQLAlchemy del repositorio de despachos."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, literal, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.dispatch import Dispatch, DispatchItem
from app.modules.inventory.domain.repositories.dispatch_repository import (
    DispatchRepository,
)
from app.modules.inventory.infrastructure.models import (
    BatchModel,
    DispatchItemModel,
    DispatchModel,
    MedicationModel,
    PrescriptionModel,
)
from app.modules.auth.infrastructure.models import UserModel
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.mixins import RecordStatus


class SQLAlchemyDispatchRepository(DispatchRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _item_to_entity(
        m: DispatchItemModel,
        medication_name: Optional[str] = None,
        medication_form: Optional[str] = None,
        batch_number: Optional[str] = None,
        expiration_date: Optional[str] = None,
    ) -> DispatchItem:
        return DispatchItem(
            id=m.id,
            fk_dispatch_id=m.fk_dispatch_id,
            fk_batch_id=m.fk_batch_id,
            fk_medication_id=m.fk_medication_id,
            quantity_dispatched=m.quantity_dispatched,
            medication_name=medication_name,
            medication_form=medication_form,
            batch_number=batch_number,
            expiration_date=expiration_date,
        )

    @staticmethod
    def _row_to_item(row) -> DispatchItem:
        item_model = row[0]
        return SQLAlchemyDispatchRepository._item_to_entity(
            item_model,
            medication_name=row[1],
            medication_form=row[2],
            batch_number=row[3],
            expiration_date=row[4].isoformat() if row[4] else None,
        )

    def _items_select(self):
        """Base select for dispatch items enriched with medication + batch JOINs."""
        return (
            select(
                DispatchItemModel,
                MedicationModel.generic_name,
                MedicationModel.pharmaceutical_form,
                BatchModel.lot_number,
                BatchModel.expiration_date,
            )
            .outerjoin(MedicationModel, DispatchItemModel.fk_medication_id == MedicationModel.id)
            .outerjoin(BatchModel, DispatchItemModel.fk_batch_id == BatchModel.id)
            .where(DispatchItemModel.status == RecordStatus.ACTIVE)
        )

    @staticmethod
    def _to_entity(
        model: DispatchModel,
        items: list[DispatchItem],
        prescription_number: Optional[str] = None,
        patient_full_name: Optional[str] = None,
        pharmacist_full_name: Optional[str] = None,
    ) -> Dispatch:
        return Dispatch(
            id=model.id,
            fk_prescription_id=model.fk_prescription_id,
            fk_patient_id=model.fk_patient_id,
            fk_pharmacist_id=model.fk_pharmacist_id,
            dispatch_date=model.dispatch_date.isoformat(),
            dispatch_status=model.dispatch_status,
            notes=model.notes,
            items=items,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
            prescription_number=prescription_number,
            patient_full_name=patient_full_name,
            pharmacist_full_name=pharmacist_full_name,
        )

    async def _load_items(self, dispatch_id: str) -> list[DispatchItem]:
        """Load enriched items (medication + batch) for a single dispatch."""
        result = await self._session.execute(
            self._items_select().where(DispatchItemModel.fk_dispatch_id == dispatch_id)
        )
        return [self._row_to_item(row) for row in result.all()]

    async def _load_items_batch(
        self, dispatch_ids: list[str]
    ) -> dict[str, list[DispatchItem]]:
        """Load enriched items for multiple dispatches in a single query, grouped by dispatch id."""
        if not dispatch_ids:
            return {}
        result = await self._session.execute(
            self._items_select().where(
                DispatchItemModel.fk_dispatch_id.in_(dispatch_ids)
            )
        )
        items_by_dispatch: dict[str, list[DispatchItem]] = {
            did: [] for did in dispatch_ids
        }
        for row in result.all():
            entity = self._row_to_item(row)
            items_by_dispatch[entity.fk_dispatch_id].append(entity)
        return items_by_dispatch

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    def _enriched_dispatch_select(self):
        """Base select for a dispatch with prescription/patient/pharmacist display joins."""
        return (
            select(
                DispatchModel,
                PrescriptionModel.prescription_number,
                func.concat(PatientModel.first_name, literal(" "), PatientModel.last_name).label("patient_full_name"),
                UserModel.full_name.label("pharmacist_full_name"),
            )
            .outerjoin(PrescriptionModel, DispatchModel.fk_prescription_id == PrescriptionModel.id)
            .outerjoin(PatientModel, DispatchModel.fk_patient_id == PatientModel.id)
            .outerjoin(UserModel, DispatchModel.fk_pharmacist_id == UserModel.id)
            .where(DispatchModel.status == RecordStatus.ACTIVE)
        )

    async def find_by_id(self, id: str) -> Optional[Dispatch]:
        result = await self._session.execute(
            self._enriched_dispatch_select().where(DispatchModel.id == id)
        )
        row = result.first()
        if not row:
            return None
        items = await self._load_items(id)
        return self._to_entity(
            row[0],
            items,
            prescription_number=row[1],
            patient_full_name=row[2],
            pharmacist_full_name=row[3],
        )

    async def find_by_prescription(self, fk_prescription_id: str) -> list[Dispatch]:
        result = await self._session.execute(
            self._enriched_dispatch_select().where(
                DispatchModel.fk_prescription_id == fk_prescription_id
            )
        )
        rows = result.all()
        items_by_dispatch = await self._load_items_batch([row[0].id for row in rows])
        return [
            self._to_entity(
                row[0],
                items_by_dispatch.get(row[0].id, []),
                prescription_number=row[1],
                patient_full_name=row[2],
                pharmacist_full_name=row[3],
            )
            for row in rows
        ]

    async def find_all(
        self,
        patient_id: Optional[str] = None,
        prescription_number: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Dispatch], int]:
        # Enriched query: LEFT JOIN prescriptions, patients, users for display names
        enriched_q = (
            select(
                DispatchModel,
                PrescriptionModel.prescription_number,
                func.concat(PatientModel.first_name, literal(" "), PatientModel.last_name).label("patient_full_name"),
                UserModel.full_name.label("pharmacist_full_name"),
            )
            .outerjoin(PrescriptionModel, DispatchModel.fk_prescription_id == PrescriptionModel.id)
            .outerjoin(PatientModel, DispatchModel.fk_patient_id == PatientModel.id)
            .outerjoin(UserModel, DispatchModel.fk_pharmacist_id == UserModel.id)
            .where(DispatchModel.status == RecordStatus.ACTIVE)
        )
        count_q = select(func.count(DispatchModel.id)).where(DispatchModel.status == RecordStatus.ACTIVE)

        if patient_id:
            enriched_q = enriched_q.where(DispatchModel.fk_patient_id == patient_id)
            count_q = count_q.where(DispatchModel.fk_patient_id == patient_id)
        if prescription_number:
            enriched_q = enriched_q.where(
                PrescriptionModel.prescription_number.ilike(f"%{prescription_number}%")
            )
            count_q = count_q.join(
                PrescriptionModel, DispatchModel.fk_prescription_id == PrescriptionModel.id
            ).where(PrescriptionModel.prescription_number.ilike(f"%{prescription_number}%"))
        if status:
            enriched_q = enriched_q.where(DispatchModel.dispatch_status == status)
            count_q = count_q.where(DispatchModel.dispatch_status == status)
        if date_from:
            dt = datetime.fromisoformat(date_from)
            enriched_q = enriched_q.where(DispatchModel.dispatch_date >= dt)
            count_q = count_q.where(DispatchModel.dispatch_date >= dt)
        if date_to:
            dt = datetime.fromisoformat(date_to)
            enriched_q = enriched_q.where(DispatchModel.dispatch_date <= dt)
            count_q = count_q.where(DispatchModel.dispatch_date <= dt)

        total = (await self._session.execute(count_q)).scalar_one()
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                enriched_q.order_by(DispatchModel.dispatch_date.desc()).offset(offset).limit(page_size)
            )
        ).all()

        items_by_dispatch = await self._load_items_batch([row[0].id for row in rows])
        return [
            self._to_entity(
                row[0],
                items_by_dispatch.get(row[0].id, []),
                prescription_number=row[1],
                patient_full_name=row[2],
                pharmacist_full_name=row[3],
            )
            for row in rows
        ], total

    async def find_by_patient(
        self,
        fk_patient_id: str,
        prescription_number: Optional[str],
        status: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        page_size: int,
    ) -> tuple[list[Dispatch], int]:
        enriched_q = (
            select(
                DispatchModel,
                PrescriptionModel.prescription_number,
                func.concat(PatientModel.first_name, literal(" "), PatientModel.last_name).label("patient_full_name"),
                UserModel.full_name.label("pharmacist_full_name"),
            )
            .outerjoin(PrescriptionModel, DispatchModel.fk_prescription_id == PrescriptionModel.id)
            .outerjoin(PatientModel, DispatchModel.fk_patient_id == PatientModel.id)
            .outerjoin(UserModel, DispatchModel.fk_pharmacist_id == UserModel.id)
            .where(
                DispatchModel.fk_patient_id == fk_patient_id,
                DispatchModel.status == RecordStatus.ACTIVE,
            )
        )
        count_q = select(func.count(DispatchModel.id)).where(
            DispatchModel.fk_patient_id == fk_patient_id,
            DispatchModel.status == RecordStatus.ACTIVE,
        )

        if prescription_number:
            enriched_q = enriched_q.where(PrescriptionModel.prescription_number == prescription_number)
            count_q = count_q.join(
                PrescriptionModel, DispatchModel.fk_prescription_id == PrescriptionModel.id
            ).where(PrescriptionModel.prescription_number == prescription_number)
        if status:
            enriched_q = enriched_q.where(DispatchModel.dispatch_status == status)
            count_q = count_q.where(DispatchModel.dispatch_status == status)
        if date_from:
            dt = datetime.fromisoformat(date_from)
            enriched_q = enriched_q.where(DispatchModel.dispatch_date >= dt)
            count_q = count_q.where(DispatchModel.dispatch_date >= dt)
        if date_to:
            dt = datetime.fromisoformat(date_to)
            enriched_q = enriched_q.where(DispatchModel.dispatch_date <= dt)
            count_q = count_q.where(DispatchModel.dispatch_date <= dt)

        total = (await self._session.execute(count_q)).scalar_one()
        offset = (page - 1) * page_size
        rows = (
            await self._session.execute(
                enriched_q.order_by(DispatchModel.dispatch_date.desc()).offset(offset).limit(page_size)
            )
        ).all()

        items_by_dispatch = await self._load_items_batch([row[0].id for row in rows])
        return [
            self._to_entity(
                row[0],
                items_by_dispatch.get(row[0].id, []),
                prescription_number=row[1],
                patient_full_name=row[2],
                pharmacist_full_name=row[3],
            )
            for row in rows
        ], total

    async def get_monthly_consumption(
        self,
        fk_patient_id: str,
        fk_medication_id: str,
        month: str,
        year: int,
    ) -> int:
        """
        Suma de quantity_dispatched para un paciente/medicamento
        en un mes específico. Incluye solo despachos con status != 'cancelled'.
        """
        dispatches_in_month = (
            select(DispatchModel.id)
            .where(
                DispatchModel.fk_patient_id == fk_patient_id,
                func.extract("month", DispatchModel.dispatch_date) == int(month),
                func.extract("year", DispatchModel.dispatch_date) == year,
                DispatchModel.dispatch_status != "cancelled",
                DispatchModel.status == RecordStatus.ACTIVE,
            )
            .subquery()
        )

        q = select(
            func.coalesce(func.sum(DispatchItemModel.quantity_dispatched), 0)
        ).where(
            DispatchItemModel.fk_dispatch_id.in_(select(dispatches_in_month.c.id)),
            DispatchItemModel.fk_medication_id == fk_medication_id,
            DispatchItemModel.status == RecordStatus.ACTIVE,
        )

        result = await self._session.execute(q)
        return result.scalar_one()

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Dispatch:
        """
        Crea el registro de despacho y sus ítems en un solo flush.
        Se asume que la sesión está dentro de una transacción abierta
        (gestionada por get_db() en la capa de presentación).
        """
        items_data: list[dict] = data.pop("items", [])
        dispatch_id = str(uuid4())

        model = DispatchModel(
            id=dispatch_id,
            created_by=created_by,
            **data,
        )
        self._session.add(model)
        await self._session.flush()

        item_models = []
        for item in items_data:
            im = DispatchItemModel(
                id=str(uuid4()),
                fk_dispatch_id=dispatch_id,
                created_by=created_by,
                **item,
            )
            self._session.add(im)
            item_models.append(im)

        await self._session.flush()
        # Re-load with all enrichments (medication name, batch lot, patient, pharmacist).
        return await self.find_by_id(dispatch_id)

    async def update_status(self, id: str, new_status: str, updated_by: str) -> None:
        await self._session.execute(
            sql_update(DispatchModel)
            .where(DispatchModel.id == id)
            .values(
                dispatch_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
