from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.dtos.auth_dto import LoginDTO, RegisterDTO
from app.modules.auth.application.use_cases.login_user import LoginUserUseCase
from app.modules.auth.application.use_cases.register_user import RegisterUserUseCase
from app.modules.auth.presentation.dependencies import get_user_repo, get_role_repo
from app.modules.auth.presentation.schemas.auth_schema import (
    LoginRequest,
    PatientLoginData,
    PatientLoginRequest,
    PatientLoginResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.patients.infrastructure.models import PatientModel
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
        user_repo=get_user_repo(db),
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
        user_repo=get_user_repo(db),
        role_repo=get_role_repo(db),
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


@router.post(
    "/patient/login",
    response_model=StandardResponse[PatientLoginResponse],
)
async def patient_login(
    body: PatientLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate patient by dni or NHM (no password required)."""
    if body.query_type == "dni":
        stmt = select(PatientModel).where(
            PatientModel.dni == body.query,
            PatientModel.deleted_at.is_(None),
        )
    else:
        stmt = select(PatientModel).where(
            PatientModel.nhm == int(body.query),
            PatientModel.deleted_at.is_(None),
        )

    result = await db.execute(stmt)
    patient = result.scalars().first()

    if not patient:
        return ok(
            data=PatientLoginResponse(found=False, patient=None).model_dump(),
            message="Patient not found",
        )

    return ok(
        data=PatientLoginResponse(
            found=True,
            patient=PatientLoginData(
                id=patient.id,
                nhm=patient.nhm,
                first_name=patient.first_name,
                last_name=patient.last_name,
                university_relation=patient.university_relation,
                is_new=patient.is_new,
            ),
        ).model_dump(),
        message="Patient found",
    )
