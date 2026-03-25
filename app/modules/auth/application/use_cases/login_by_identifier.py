from __future__ import annotations

from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.modules.auth.application.dtos.auth_dto import (
    LoginByIdentifierDTO,
    TokenResponseDTO,
)
from app.modules.auth.domain.repositories.user_repository import UserRepository


class LoginByIdentifierUseCase:
    """Autentica un usuario con identifier (email, cédula o username) + password.

    Intenta resolver el identifier en orden: cédula → email → username.
    Complejidad: O(log n) — hasta 3 lookups por índice, cada uno O(log n).
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, dto: LoginByIdentifierDTO) -> TokenResponseDTO:
        identifier = dto.identifier.strip()

        # Intentar por cédula primero (formato V-12345678)
        user = await self._user_repo.get_by_cedula(identifier)

        # Si no, intentar por email
        if user is None and "@" in identifier:
            user = await self._user_repo.get_by_email(identifier)

        # Si no, intentar por username
        if user is None:
            user = await self._user_repo.get_by_email(identifier)
            if user is None:
                user = await self._user_repo.get_by_username(identifier)

        if user is None:
            raise UnauthorizedException("Credenciales inválidas")

        if not user.hashed_password:
            raise UnauthorizedException("Este usuario usa autenticación externa")

        if not verify_password(dto.password, user.hashed_password):
            raise UnauthorizedException("Credenciales inválidas")

        if user.user_status == "SUSPENDED":
            raise UnauthorizedException("Usuario suspendido")

        token = create_access_token(data={"sub": user.id, "email": user.email})

        return TokenResponseDTO(access_token=token)
