"""Interfaz abstracta del repositorio de órdenes de compra."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.inventory.domain.entities.purchase_order import (
    PurchaseOrder,
    PurchaseOrderItem,
)


class PurchaseOrderRepository(ABC):

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[PurchaseOrder]:
        """Retorna la orden con su lista de ítems, o None si no existe."""
        ...

    @abstractmethod
    async def find_item_by_id(self, item_id: str) -> Optional[PurchaseOrderItem]:
        """Retorna un ítem de orden por su ID, o None si no existe."""
        ...

    @abstractmethod
    async def update_order_status(
        self, id: str, status: str, updated_by: str
    ) -> None:
        """Actualiza el estado de la orden de compra."""
        ...

    @abstractmethod
    async def increment_item_received(
        self,
        item_id: str,
        quantity_delta: int,
        item_status: str,
        unit_cost: Optional[float],
        updated_by: str,
    ) -> None:
        """Incrementa quantity_received del ítem usando una operación DB-side
        para evitar condiciones de carrera en recepciones concurrentes."""
        ...

    @abstractmethod
    async def all_items_received(self, order_id: str) -> bool:
        """Retorna True si todos los ítems activos de la orden tienen
        item_status == 'received'."""
        ...
