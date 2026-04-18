from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.modules.auth.application.dtos.auth_dto import LoginDTO, RegisterDTO
from app.modules.auth.application.use_cases.login_user import LoginUserUseCase
from app.modules.auth.application.use_cases.register_user import RegisterUserUseCase
from app.modules.auth.infrastructure.repositories.revoked_token_repository import (
    RevokedTokenRepository,
)
from app.modules.auth.presentation.dependencies import get_user_repo, get_role_repo
from app.modules.auth.presentation.schemas.auth_schema import (
    LoginRequest,
    PatientLoginData,
    PatientLoginRequest,
    PatientLoginResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.session import get_db
from app.shared.schemas.common import StandardResponse
from app.shared.schemas.responses import created, ok

router = APIRouter(prefix="/auth", tags=["Auth"])

_security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=StandardResponse[TokenResponse])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email and password (local provider)."""
    use_case = LoginUserUseCase(
        user_repo=get_user_repo(db),
    )
    result = await use_case.execute(
        LoginDTO(email=body.email, password=body.password)
    )
    return ok(
        data=TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            expires_in=result.expires_in,
        ).model_dump(),
        message="Login successful",
    )


@router.post("/logout", response_model=StandardResponse[dict])
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
    x_refresh_token: str | None = Header(default=None, alias="X-Refresh-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the caller's access token (and optional refresh via header).

    Idempotent — re-calling with an already-revoked or expired token is a noop.
    Anonymous / missing-token requests are also noop to avoid leaking auth state.
    """
    repo = RevokedTokenRepository(db)

    # Access token: from Authorization header
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload and payload.get("jti") and payload.get("sub"):
            exp_ts = payload.get("exp")
            expires_at = (
                datetime.fromtimestamp(exp_ts, tz=timezone.utc)
                if isinstance(exp_ts, (int, float))
                else datetime.now(timezone.utc)
            )
            await repo.revoke(
                jti=payload["jti"],
                user_id=payload["sub"],
                expires_at=expires_at,
                token_type=payload.get("type", ACCESS_TOKEN_TYPE),
            )

    # Refresh token: optional, from X-Refresh-Token header
    if x_refresh_token:
        rp = decode_access_token(x_refresh_token)
        if rp and rp.get("jti") and rp.get("sub"):
            exp_ts = rp.get("exp")
            expires_at = (
                datetime.fromtimestamp(exp_ts, tz=timezone.utc)
                if isinstance(exp_ts, (int, float))
                else datetime.now(timezone.utc)
            )
            await repo.revoke(
                jti=rp["jti"],
                user_id=rp["sub"],
                expires_at=expires_at,
                token_type=rp.get("type", REFRESH_TOKEN_TYPE),
            )

    return ok(data={"revoked": True}, message="Logout successful")


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new access+refresh pair.

    Rota el refresh token — el viejo queda revocado. Si el refresh recibido
    ya está en revoked_tokens, devuelve 401 (posible replay).
    """
    settings = get_settings()
    repo = RevokedTokenRepository(db)

    payload = decode_access_token(body.refresh_token)
    if payload is None:
        raise UnauthorizedException("Refresh token inválido o expirado")
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise UnauthorizedException("Token no es de refresh")

    jti = payload.get("jti")
    sub = payload.get("sub")
    email = payload.get("email", "")
    if not jti or not sub:
        raise UnauthorizedException("Refresh token sin identificadores")

    if await repo.is_revoked(jti):
        raise UnauthorizedException("Refresh token revocado")

    # Rotar: revocar el refresh usado antes de emitir uno nuevo
    exp_ts = payload.get("exp")
    prior_expires = (
        datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        if isinstance(exp_ts, (int, float))
        else datetime.now(timezone.utc)
    )
    await repo.revoke(
        jti=jti,
        user_id=sub,
        expires_at=prior_expires,
        token_type=REFRESH_TOKEN_TYPE,
    )

    access, _, _ = create_access_token(data={"sub": sub, "email": email})
    new_refresh, _, _ = create_refresh_token(data={"sub": sub, "email": email})

    return ok(
        data=TokenResponse(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ).model_dump(),
        message="Token refreshed",
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
    """Register a new user. Assigns the 'paciente' role by default."""
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
        message="User registered successfully",
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
