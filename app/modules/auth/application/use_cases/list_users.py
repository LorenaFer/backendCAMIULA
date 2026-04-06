from __future__ import annotations

from typing import Tuple

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    """List users with paginatión.

    Complejidad: O(log n + k) — COUNT indexado + SELECT LIMIT k.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self, page: int, page_size: int
    ) -> Tuple[list[User], int]:
        return await self._user_repo.list_paginated(page, page_size)
