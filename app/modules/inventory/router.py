"""Router principal del módulo de Inventario.

Agrega todos los sub-routers bajo el prefijo /inventory.
Registrar en app/main.py:

    from app.modules.inventory.router import router as inventory_router
    app.include_router(inventory_router, prefix="/api")
"""

from fastapi import APIRouter

from app.modules.inventory.presentation.routes.batches_router import (
    router as batches_router,
)
from app.modules.inventory.presentation.routes.dispatches_router import (
    router as dispatches_router,
)
from app.modules.inventory.presentation.routes.limits_router import (
    router as limits_router,
)
from app.modules.inventory.presentation.routes.medications_router import (
    router as medications_router,
)
from app.modules.inventory.presentation.routes.prescriptions_router import (
    router as prescriptions_router,
)
from app.modules.inventory.presentation.routes.purchase_orders_router import (
    router as purchase_orders_router,
)
from app.modules.inventory.presentation.routes.reports_router import (
    router as reports_router,
)
from app.modules.inventory.presentation.routes.suppliers_router import (
    router as suppliers_router,
)

router = APIRouter(prefix="/inventory")

router.include_router(medications_router)
router.include_router(suppliers_router)
router.include_router(purchase_orders_router)
router.include_router(batches_router)
router.include_router(prescriptions_router)
router.include_router(dispatches_router)
router.include_router(limits_router)
router.include_router(reports_router)
