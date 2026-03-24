from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.auth.domain.entities.role import Role


class RoleRepository(ABC):

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Role]:
        ...

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        ...

    @abstractmethod
    async def list_all(self) -> list[Role]:
        ...

    @abstractmethod
    async def assign_role_to_user(
        self, user_id: str, role_id: str, assigned_by: Optional[str] = None
    ) -> None:
        ...

    @abstractmethod
    async def remove_role_from_user(
        self, user_id: str, role_id: str, removed_by: Optional[str] = None
    ) -> None:
        ...
