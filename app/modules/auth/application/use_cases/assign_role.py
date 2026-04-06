from __future__ import annotations

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.auth.application.dtos.user_dto import AssignRoleDTO
from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.domain.repositories.user_repository import UserRepository


class AssignRoleUseCase:
    """Assign a role to a user.

    Complejidad: O(log n) — verify user + verify role + INSERT junction.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        permission_cache: object = None,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._cache = permission_cache

    async def execute(self, dto: AssignRoleDTO, assigned_by: str) -> None:
        user = await self._user_repo.get_by_id(dto.user_id)
        if user is None:
            raise NotFoundException("Usuario not found")

        role = await self._role_repo.get_by_name(dto.role_name)
        if role is None:
            raise NotFoundException(f"Rol '{dto.role_name}' not found")

        existing_roles = await self._user_repo.get_user_roles(dto.user_id)
        if dto.role_name in existing_roles:
            raise ConflictException("El usuario ya tiene este rol asignado")

        await self._role_repo.assign_role_to_user(
            user_id=dto.user_id,
            role_id=role.id,
            assigned_by=assigned_by,
        )

        # Invalidar cache para que el próximo request recargue permisos
        if self._cache is not None:
            self._cache.invalidate(dto.user_id)
