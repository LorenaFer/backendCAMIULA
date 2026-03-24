from __future__ import annotations

from typing import Optional

from app.core.exceptions import ConflictException
from app.core.security import hash_password
from app.modules.auth.application.dtos.auth_dto import RegisterDTO
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.domain.repositories.user_repository import UserRepository


class RegisterUserUseCase:
    """Registra un nuevo usuario y le asigna el rol 'paciente' por defecto.

    Complejidad: O(log n) — check email + INSERT + assign role.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
    ) -> None:
        self._user_repo = user_repo
        self._role_repo = role_repo

    async def execute(
        self, dto: RegisterDTO, registered_by: Optional[str] = None
    ) -> User:
        existing = await self._user_repo.get_by_email(dto.email)
        if existing is not None:
            raise ConflictException("Ya existe un usuario con ese email")

        user = User(
            email=dto.email,
            full_name=dto.full_name,
            phone=dto.phone,
            hashed_password=hash_password(dto.password),
            user_status="ACTIVE",
        )

        user = await self._user_repo.create(user)

        default_role = await self._role_repo.get_by_name("paciente")
        if default_role:
            await self._role_repo.assign_role_to_user(
                user_id=user.id,
                role_id=default_role.id,
                assigned_by=registered_by,
            )
            user.roles = ["paciente"]

        return user
