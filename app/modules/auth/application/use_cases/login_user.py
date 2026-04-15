from __future__ import annotations

from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.core.config import get_settings
from app.modules.auth.application.dtos.auth_dto import LoginDTO, TokenResponseDTO
from app.modules.auth.domain.repositories.user_repository import UserRepository


class LoginUserUseCase:
    """Authenticate a user with email and password (LocalAuthProvider).

    Emite par access+refresh. El access es de vida corta (~15 min) y el
    refresh de vida larga (~7 días); el frontend rota el refresh en cada
    uso para limitar la ventana si se filtra.

    Complejidad: O(log n) — lookup por email indexado + bcrypt verify O(1).
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo
        self._settings = get_settings()

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

        access, _, _ = create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        refresh, _, _ = create_refresh_token(
            data={"sub": user.id, "email": user.email}
        )

        return TokenResponseDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
