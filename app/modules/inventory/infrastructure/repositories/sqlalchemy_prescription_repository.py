"""Implementación SQLAlchemy del repositorio de recetas médicas."""

from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities.prescription import (
    Prescription,
    PrescriptionItem,
)
from app.modules.inventory.domain.repositories.prescription_repository import (
    PrescriptionRepository,
)
from app.modules.inventory.infrastructure.models import (
    PrescriptionItemModel,
    PrescriptionModel,
)
from app.shared.database.mixins import RecordStatus


class SQLAlchemyPrescriptionRepository(PrescriptionRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────────────────
    # Conversión
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _item_to_entity(m: PrescriptionItemModel) -> PrescriptionItem:
        from app.modules.inventory.domain.entities.prescription import MedicationEmbed

        med_embed = None
        if hasattr(m, "medication") and m.medication:
            med = m.medication
            med_embed = MedicationEmbed(
                id=med.id,
                code=med.code,
                generic_name=med.generic_name,
                pharmaceutical_form=med.pharmaceutical_form,
                unit_measure=med.unit_measure,
            )
        return PrescriptionItem(
            id=m.id,
            fk_prescription_id=m.fk_prescription_id,
            fk_medication_id=m.fk_medication_id,
            quantity_prescribed=m.quantity_prescribed,
            quantity_dispatched=m.quantity_dispatched,
            item_status=m.item_status,
            dosage_instructions=m.dosage_instructions,
            duration_days=m.duration_days,
            medication=med_embed,
        )

    def _model_to_entity(
        self, model: PrescriptionModel, doctor_name: Optional[str] = None
    ) -> Prescription:
        items = [
            self._item_to_entity(m) for m in (model.items_rel or [])
        ]
        return Prescription(
            id=model.id,
            fk_appointment_id=model.fk_appointment_id,
            fk_patient_id=model.fk_patient_id,
            fk_doctor_id=model.fk_doctor_id,
            prescription_number=model.prescription_number,
            prescription_date=model.prescription_date.isoformat() if model.prescription_date else None,
            prescription_status=model.prescription_status,
            notes=model.notes,
            doctor_name=doctor_name,
            items=items,
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    @staticmethod
    def _to_entity(
        model: PrescriptionModel, items: list[PrescriptionItemModel]
    ) -> Prescription:
        return Prescription(
            id=model.id,
            fk_appointment_id=model.fk_appointment_id,
            fk_patient_id=model.fk_patient_id,
            fk_doctor_id=model.fk_doctor_id,
            prescription_number=model.prescription_number,
            prescription_date=model.prescription_date.isoformat() if model.prescription_date else None,
            prescription_status=model.prescription_status,
            notes=model.notes,
            items=[SQLAlchemyPrescriptionRepository._item_to_entity(i) for i in items],
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def _resolve_doctor_name(self, doctor_id: str) -> Optional[str]:
        """Resolve doctor name from doctors table (cross-module)."""
        from sqlalchemy import text
        result = await self._session.execute(
            text("SELECT first_name || ' ' || last_name FROM doctors WHERE fk_user_id = :uid OR id = :uid LIMIT 1"),
            {"uid": doctor_id},
        )
        row = result.fetchone()
        return row[0] if row else None

    async def _enrich(self, model: PrescriptionModel) -> Prescription:
        """Convert model to entity with medication JOINs and doctor name."""
        doctor_name = await self._resolve_doctor_name(model.fk_doctor_id)
        return self._model_to_entity(model, doctor_name=doctor_name)

    async def _load_items(self, prescription_id: str) -> list[PrescriptionItemModel]:
        result = await self._session.execute(
            select(PrescriptionItemModel).where(
                PrescriptionItemModel.fk_prescription_id == prescription_id,
                PrescriptionItemModel.status == RecordStatus.ACTIVE,
            )
        )
        return result.scalars().all()

    # ──────────────────────────────────────────────────────────
    # Consultas
    # ──────────────────────────────────────────────────────────

    async def find_by_id(self, id: str) -> Optional[Prescription]:
        result = await self._session.execute(
            select(PrescriptionModel).where(
                PrescriptionModel.id == id,
                PrescriptionModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.unique().scalar_one_or_none()
        if not m:
            return None
        return await self._enrich(m)

    async def find_by_appointment(self, fk_appointment_id: str) -> Optional[Prescription]:
        result = await self._session.execute(
            select(PrescriptionModel).where(
                PrescriptionModel.fk_appointment_id == fk_appointment_id,
                PrescriptionModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.unique().scalar_one_or_none()
        if not m:
            return None
        return await self._enrich(m)

    async def find_by_patient(
        self, fk_patient_id: str, page: int, page_size: int
    ) -> tuple[list[Prescription], int]:
        q = select(PrescriptionModel).where(
            PrescriptionModel.fk_patient_id == fk_patient_id,
            PrescriptionModel.status == RecordStatus.ACTIVE,
        )
        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()
        offset = (page - 1) * page_size
        result = await self._session.execute(
            q.order_by(PrescriptionModel.prescription_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        prescriptions = []
        for m in result.unique().scalars().all():
            prescriptions.append(await self._enrich(m))
        return prescriptions, total

    async def find_by_number(self, prescription_number: str) -> Optional[Prescription]:
        result = await self._session.execute(
            select(PrescriptionModel).where(
                PrescriptionModel.prescription_number == prescription_number,
                PrescriptionModel.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        if not m:
            return None
        items = await self._load_items(m.id)
        return self._to_entity(m, items)

    async def get_next_number(self) -> str:
        year = date.today().year
        result = await self._session.execute(
            select(func.count(PrescriptionModel.id)).where(
                func.extract("year", PrescriptionModel.prescription_date) == year
            )
        )
        count = result.scalar_one() + 1
        return f"PRX-{year}-{count:04d}"

    # ──────────────────────────────────────────────────────────
    # Escritura
    # ──────────────────────────────────────────────────────────

    async def create(self, data: dict, created_by: str) -> Prescription:
        # Convert prescription_date string to date object for asyncpg
        if isinstance(data.get("prescription_date"), str):
            from datetime import date as date_type
            data["prescription_date"] = date_type.fromisoformat(data["prescription_date"])

        items_data: list[dict] = data.pop("items", [])
        prescription_id = str(uuid4())

        model = PrescriptionModel(id=prescription_id, created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()

        item_models = []
        for item in items_data:
            im = PrescriptionItemModel(
                id=str(uuid4()),
                fk_prescription_id=prescription_id,
                created_by=created_by,
                **item,
            )
            self._session.add(im)
            item_models.append(im)

        await self._session.flush()
        # Re-fetch with eager-loaded relationships
        return await self.find_by_id(prescription_id)

    async def update_status(self, id: str, new_status: str, updated_by: str) -> None:
        await self._session.execute(
            sql_update(PrescriptionModel)
            .where(PrescriptionModel.id == id)
            .values(
                prescription_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )

    async def update_item_dispatched(
        self,
        item_id: str,
        new_dispatched: int,
        prescribed: int,
        updated_by: str,
    ) -> None:
        """Actualiza quantity_dispatched e item_status de un ítem."""
        new_status = (
            "dispensed" if new_dispatched >= prescribed else "partial"
        )
        await self._session.execute(
            sql_update(PrescriptionItemModel)
            .where(PrescriptionItemModel.id == item_id)
            .values(
                quantity_dispatched=new_dispatched,
                item_status=new_status,
                updated_at=datetime.now(timezone.utc),
                updated_by=updated_by,
            )
        )
