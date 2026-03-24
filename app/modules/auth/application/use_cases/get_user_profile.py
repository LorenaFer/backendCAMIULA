from __future__ import annotations

from app.core.exceptions import NotFoundException
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.user_repository import UserRepository


class GetUserProfileUseCase:
    """Obtiene el perfil de un usuario con sus roles.

    Complejidad: O(log n) — lookup por ID indexado.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, user_id: str) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundException("Usuario no encontrado")

        user.roles = await self._user_repo.get_user_roles(user_id)
        return user
