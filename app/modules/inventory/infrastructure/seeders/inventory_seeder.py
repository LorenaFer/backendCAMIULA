"""
Seeder del módulo de Inventario — CAMIULA / ULA.

Inserta los datos iniciales de referencia del sistema:
  - 2 proveedores activos
  - 3 medicamentos del catálogo inicial
  - 2 lotes de Amoxicilina (vencimiento próximo y lejano)
  - Límites de despacho globales para cada medicamento

Los IDs son UUIDs fijos para facilitar referencias entre seeders
y para que el frontend pueda operar con datos predictivos en desarrollo.

Ejecución:
    python -m app.shared.database.seeder inventory
    python -m app.shared.database.seeder inventory --fresh
"""

from datetime import date
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.infrastructure.models import (
    BatchModel,
    DispatchLimitModel,
    MedicationModel,
    SupplierModel,
)
from app.shared.database.seeder import BaseSeeder


# ─── IDs fijos para desarrollo ───────────────────────────────

_SUPPLIER_DMC_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_SUPPLIER_ROCHE_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"

_MED_AMOXICILINA_ID = "c3d4e5f6-a7b8-9012-cdef-123456789012"
_MED_IBUPROFENO_ID = "d4e5f6a7-b8c9-0123-defa-234567890123"
_MED_METFORMINA_ID = "e5f6a7b8-c9d0-1234-efab-345678901234"

_BATCH_AMOX_NEAR_ID = "f6a7b8c9-d0e1-2345-fabc-456789012345"
_BATCH_AMOX_FAR_ID = "a7b8c9d0-e1f2-3456-abcd-567890123456"

_LIMIT_AMOX_ID = "b8c9d0e1-f2a3-4567-bcde-678901234567"
_LIMIT_IBUP_ID = "c9d0e1f2-a3b4-5678-cdef-789012345678"
_LIMIT_METF_ID = "d0e1f2a3-b4c5-6789-defa-890123456789"


class InventorySeeder(BaseSeeder):
    """Siembra el catálogo base del módulo de Inventario."""

    order = 40  # Ejecutar después del seeder de usuarios (order=10).

    async def run(self, session: AsyncSession) -> None:
        await self._seed_suppliers(session)
        await self._seed_medications(session)
        await self._seed_batches(session)
        await self._seed_dispatch_limits(session)
        print("  [inventory] Proveedores, medicamentos, lotes y límites insertados.")

    async def clear(self, session: AsyncSession) -> None:
        for model in (
            DispatchLimitModel,
            BatchModel,
            MedicationModel,
            SupplierModel,
        ):
            await session.execute(delete(model))
        print("  [inventory] Tablas limpiadas.")

    # ──────────────────────────────────────────────────────────
    # Proveedores
    # ──────────────────────────────────────────────────────────

    async def _seed_suppliers(self, session: AsyncSession) -> None:
        existing = await session.get(SupplierModel, _SUPPLIER_DMC_ID)
        if existing:
            return

        suppliers = [
            SupplierModel(
                id=_SUPPLIER_DMC_ID,
                name="Distribuidora Médica Caracas",
                rif="J-30123456-7",
                phone="0212-555-1234",
                email="ventas@dmc.com.ve",
                contact_name="Carlos Rodríguez",
                payment_terms="30 días neto",
                supplier_status="active",
                created_by="system",
            ),
            SupplierModel(
                id=_SUPPLIER_ROCHE_ID,
                name="Laboratorios Roche Venezuela",
                rif="J-00012345-6",
                phone="0212-555-5678",
                email="info@roche.com.ve",
                contact_name="Ana Martínez",
                payment_terms="60 días neto",
                supplier_status="active",
                created_by="system",
            ),
        ]
        session.add_all(suppliers)
        await session.flush()

    # ──────────────────────────────────────────────────────────
    # Medicamentos
    # ──────────────────────────────────────────────────────────

    async def _seed_medications(self, session: AsyncSession) -> None:
        existing = await session.get(MedicationModel, _MED_AMOXICILINA_ID)
        if existing:
            return

        medications = [
            MedicationModel(
                id=_MED_AMOXICILINA_ID,
                code="MED-001",
                generic_name="Amoxicilina",
                commercial_name="Amoxil",
                pharmaceutical_form="Cápsulas",
                concentration="500mg",
                unit_measure="Cápsulas",
                therapeutic_class="Antibiótico",
                controlled_substance=False,
                requires_refrigeration=False,
                medication_status="active",
                created_by="system",
            ),
            MedicationModel(
                id=_MED_IBUPROFENO_ID,
                code="MED-002",
                generic_name="Ibuprofeno",
                commercial_name="Advil",
                pharmaceutical_form="Tabletas",
                concentration="600mg",
                unit_measure="Tabletas",
                therapeutic_class="Analgésico",
                controlled_substance=False,
                requires_refrigeration=False,
                medication_status="active",
                created_by="system",
            ),
            MedicationModel(
                id=_MED_METFORMINA_ID,
                code="MED-003",
                generic_name="Metformina",
                commercial_name="Glucophage",
                pharmaceutical_form="Tabletas",
                concentration="850mg",
                unit_measure="Tabletas",
                therapeutic_class="Hipoglucemiante",
                controlled_substance=False,
                requires_refrigeration=False,
                medication_status="active",
                created_by="system",
            ),
        ]
        session.add_all(medications)
        await session.flush()

    # ──────────────────────────────────────────────────────────
    # Lotes — Amoxicilina (uno próximo a vencer, uno lejano)
    # ──────────────────────────────────────────────────────────

    async def _seed_batches(self, session: AsyncSession) -> None:
        existing = await session.get(BatchModel, _BATCH_AMOX_NEAR_ID)
        if existing:
            return

        batches = [
            BatchModel(
                id=_BATCH_AMOX_NEAR_ID,
                fk_medication_id=_MED_AMOXICILINA_ID,
                fk_supplier_id=_SUPPLIER_DMC_ID,
                lot_number="LOT-2026-AMX-001",
                expiration_date=date(2026, 5, 15),       # vence en ~50 días
                quantity_received=100,
                quantity_available=100,
                unit_cost=2.50,
                received_at=date(2026, 1, 10),
                batch_status="available",
                created_by="system",
            ),
            BatchModel(
                id=_BATCH_AMOX_FAR_ID,
                fk_medication_id=_MED_AMOXICILINA_ID,
                fk_supplier_id=_SUPPLIER_DMC_ID,
                lot_number="LOT-2026-AMX-002",
                expiration_date=date(2027, 12, 31),       # vence en ~21 meses
                quantity_received=200,
                quantity_available=200,
                unit_cost=2.45,
                received_at=date(2026, 2, 20),
                batch_status="available",
                created_by="system",
            ),
        ]
        session.add_all(batches)
        await session.flush()

    # ──────────────────────────────────────────────────────────
    # Límites de despacho globales
    # ──────────────────────────────────────────────────────────

    async def _seed_dispatch_limits(self, session: AsyncSession) -> None:
        existing = await session.get(DispatchLimitModel, _LIMIT_AMOX_ID)
        if existing:
            return

        limits = [
            DispatchLimitModel(
                id=_LIMIT_AMOX_ID,
                fk_medication_id=_MED_AMOXICILINA_ID,
                monthly_max_quantity=42,   # 2 ciclos de 21 cápsulas
                applies_to="all",
                active=True,
                created_by="system",
            ),
            DispatchLimitModel(
                id=_LIMIT_IBUP_ID,
                fk_medication_id=_MED_IBUPROFENO_ID,
                monthly_max_quantity=60,
                applies_to="all",
                active=True,
                created_by="system",
            ),
            DispatchLimitModel(
                id=_LIMIT_METF_ID,
                fk_medication_id=_MED_METFORMINA_ID,
                monthly_max_quantity=60,
                applies_to="all",
                active=True,
                created_by="system",
            ),
        ]
        session.add_all(limits)
        await session.flush()
