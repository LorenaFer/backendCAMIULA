from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.dtos.auth_dto import (
    LoginByIdentifierDTO,
    LoginDTO,
    RegisterDTO,
)
from app.modules.auth.application.use_cases.login_by_identifier import (
    LoginByIdentifierUseCase,
)
from app.modules.auth.application.use_cases.login_user import LoginUserUseCase
from app.modules.auth.application.use_cases.register_user import RegisterUserUseCase
from app.modules.auth.infrastructure.repositories.sqlalchemy_role_repository import (
    SQLAlchemyRoleRepository,
)
from app.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.modules.auth.presentation.schemas.auth_schema import (
    LoginByIdentifierRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.presentation.utils import build_me_response
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id
from app.shared.schemas.common import StandardResponse
from app.shared.schemas.responses import created, ok


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=StandardResponse[LoginResponse])
async def login(
    body: LoginByIdentifierRequest,
    db: AsyncSession = Depends(get_db),
):
    """Autenticar usuario con identifier (email, cédula o username) y password."""
    repo = SQLAlchemyUserRepository(db)
    use_case = LoginByIdentifierUseCase(user_repo=repo)
    result = await use_case.execute(
        LoginByIdentifierDTO(
            identifier=body.identifier,
            password=body.password,
        )
    )

    return ok(
        data=LoginResponse(
            user=MeResponse(**build_me_response(result.user)),
            token=result.token.access_token,
        ).model_dump(),
        message="Login exitoso",
    )


@router.post("/login/email", response_model=StandardResponse[TokenResponse])
async def login_by_email(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Autenticar usuario con email y password (retrocompatible)."""
    use_case = LoginUserUseCase(
        user_repo=SQLAlchemyUserRepository(db),
    )
    result = await use_case.execute(
        LoginDTO(email=body.email, password=body.password)
    )
    return ok(
        data=TokenResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
        ).model_dump(),
        message="Login exitoso",
    )


@router.post(
    "/register",
    status_code=201,
    response_model=StandardResponse[UserResponse],
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registrar nuevo usuario. Se asigna rol 'paciente' por defecto."""
    use_case = RegisterUserUseCase(
        user_repo=SQLAlchemyUserRepository(db),
        role_repo=SQLAlchemyRoleRepository(db),
    )
    user = await use_case.execute(
        RegisterDTO(
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            phone=body.phone,
        )
    )
    return created(
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            user_status=user.user_status,
            roles=user.roles,
        ).model_dump(),
        message="Usuario registrado exitosamente",
    )


@router.post("/logout", response_model=StandardResponse[None])
async def logout(
    _: str = Depends(get_current_user_id),
):
    """Cerrar sesión. El frontend elimina el token localmente."""
    return ok(data={"ok": True}, message="Sesión cerrada")
