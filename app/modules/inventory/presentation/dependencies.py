"""Dependency injection factories for the Inventory module.

This module has the most repositories (9+). Routers must use these
factories via Depends() instead of instantiating repos directly.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.repositories.batch_repository import BatchRepository
from app.modules.inventory.domain.repositories.dispatch_repository import (
    DispatchRepository,
)
from app.modules.inventory.domain.repositories.limit_repository import LimitRepository
from app.modules.inventory.domain.repositories.medication_repository import (
    MedicationRepository,
)
from app.modules.inventory.domain.repositories.prescription_repository import (
    PrescriptionRepository,
)
from app.modules.inventory.domain.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from app.modules.inventory.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_batch_repository import (
    SQLAlchemyBatchRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_dispatch_repository import (
    SQLAlchemyDispatchRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_limit_repository import (
    SQLAlchemyLimitRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_medication_repository import (
    SQLAlchemyMedicationRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_movement_repository import (
    SQLAlchemyMovementRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_prescription_repository import (
    SQLAlchemyPrescriptionRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_purchase_order_repository import (
    SQLAlchemyPurchaseOrderRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_report_repository import (
    SQLAlchemyReportRepository,
)
from app.modules.inventory.infrastructure.repositories.sqlalchemy_supplier_repository import (
    SQLAlchemySupplierRepository,
)
from app.shared.database.session import get_db


def get_medication_repo(
    session: AsyncSession = Depends(get_db),
) -> MedicationRepository:
    return SQLAlchemyMedicationRepository(session)


def get_supplier_repo(
    session: AsyncSession = Depends(get_db),
) -> SupplierRepository:
    return SQLAlchemySupplierRepository(session)


def get_batch_repo(
    session: AsyncSession = Depends(get_db),
) -> BatchRepository:
    return SQLAlchemyBatchRepository(session)


def get_prescription_repo(
    session: AsyncSession = Depends(get_db),
) -> PrescriptionRepository:
    return SQLAlchemyPrescriptionRepository(session)


def get_purchase_order_repo(
    session: AsyncSession = Depends(get_db),
) -> PurchaseOrderRepository:
    return SQLAlchemyPurchaseOrderRepository(session)


def get_dispatch_repo(
    session: AsyncSession = Depends(get_db),
) -> DispatchRepository:
    return SQLAlchemyDispatchRepository(session)


def get_limit_repo(
    session: AsyncSession = Depends(get_db),
) -> LimitRepository:
    return SQLAlchemyLimitRepository(session)


def get_report_repo(
    session: AsyncSession = Depends(get_db),
) -> SQLAlchemyReportRepository:
    return SQLAlchemyReportRepository(session)


def get_movement_repo(
    session: AsyncSession = Depends(get_db),
) -> SQLAlchemyMovementRepository:
    return SQLAlchemyMovementRepository(session)
