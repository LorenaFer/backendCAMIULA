from __future__ import annotations

from app.core.exceptions import UnauthorizedException
from app.core.security import create_access_token, verify_password
from app.modules.auth.application.dtos.auth_dto import LoginDTO, TokenResponseDTO
from app.modules.auth.domain.repositories.user_repository import UserRepository


class LoginUserUseCase:
    """Authenticate a user with email and password (LocalAuthProvider).

    Para Auth0, el frontend maneja el login y envía el JWT directamente.

    Complejidad: O(log n) — lookup por email indexado + bcrypt verify O(1).
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, dto: LoginDTO) -> TokenResponseDTO:
        user = await self._user_repo.get_by_email(dto.email)
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
