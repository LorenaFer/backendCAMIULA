from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.dtos.auth_dto import LoginDTO, RegisterDTO
from app.modules.auth.application.use_cases.login_user import LoginUserUseCase
from app.modules.auth.application.use_cases.register_user import RegisterUserUseCase
from app.modules.auth.infrastructure.repositories.sqlalchemy_role_repository import (
    SQLAlchemyRoleRepository,
)
from app.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.modules.auth.presentation.schemas.auth_schema import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.shared.database.session import get_db
from app.shared.schemas.common import StandardResponse
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Autenticar usuario con email y password (proveedor local)."""
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
