from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.modules.auth.application.dtos.user_dto import AssignRoleDTO
from app.modules.auth.application.use_cases.assign_role import AssignRoleUseCase
from app.modules.auth.application.use_cases.get_user_profile import (
    GetUserProfileUseCase,
)
from app.modules.auth.application.use_cases.list_users import ListUsersUseCase
from app.modules.auth.domain.entities.user import User
from app.modules.auth.infrastructure.repositories.sqlalchemy_role_repository import (
    SQLAlchemyRoleRepository,
)
from app.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.modules.auth.presentation.schemas.auth_schema import (
    AssignRoleRequest,
    MeResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.modules.auth.presentation.utils import build_me_response
from app.shared.database.session import get_db
from app.shared.middleware.auth import require_permission
from app.shared.middleware.permission_cache import permission_cache
from app.shared.schemas.common import PaginatedData, StandardResponse
from app.shared.schemas.responses import ok, paginated

router = APIRouter(prefix="/users", tags=["Users"])


def _to_response(user: User) -> dict:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        user_status=user.user_status,
        roles=user.roles,
    ).model_dump()


@router.get("/me", response_model=StandardResponse[MeResponse])
async def get_my_profile(
    user: User = Depends(require_permission("profile:read")),
):
    """Obtener perfil del usuario autenticado (formato contrato frontend)."""
    return ok(data=build_me_response(user), message="Perfil obtenido")


@router.put("/me", response_model=StandardResponse[UserResponse])
async def update_my_profile(
    body: UpdateProfileRequest,
    user: User = Depends(require_permission("profile:update")),
    db: AsyncSession = Depends(get_db),
):
    """Actualizar perfil propio."""
    repo = SQLAlchemyUserRepository(db)

    if body.full_name is not None:
        user.full_name = body.full_name
    if body.phone is not None:
        user.phone = body.phone

    updated = await repo.update(user)
    updated.roles = user.roles
    return ok(data=_to_response(updated), message="Perfil actualizado")


@router.get("", response_model=StandardResponse[PaginatedData[UserResponse]])
async def list_users(
    _: User = Depends(require_permission("users:read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Listar usuarios con paginación. Requiere users:read."""
    repo = SQLAlchemyUserRepository(db)
    use_case = ListUsersUseCase(user_repo=repo)
    users, total = await use_case.execute(page, page_size)

    items = []
    for u in users:
        u.roles = await repo.get_user_roles(u.id)
        items.append(_to_response(u))

    return paginated(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message="Listado de usuarios",
    )


@router.get("/{user_id}", response_model=StandardResponse[UserResponse])
async def get_user(
    user_id: str,
    _: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """Obtener un usuario por ID. Requiere users:read."""
    use_case = GetUserProfileUseCase(user_repo=SQLAlchemyUserRepository(db))
    user = await use_case.execute(user_id)
    return ok(data=_to_response(user), message="Usuario obtenido")


@router.post(
    "/{user_id}/roles",
    status_code=201,
    response_model=StandardResponse[None],
)
async def assign_role(
    user_id: str,
    body: AssignRoleRequest,
    current_user: User = Depends(require_permission("roles:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Asignar un rol a un usuario. Requiere roles:assign."""
    use_case = AssignRoleUseCase(
        user_repo=SQLAlchemyUserRepository(db),
        role_repo=SQLAlchemyRoleRepository(db),
        permission_cache=permission_cache,
    )
    await use_case.execute(
        dto=AssignRoleDTO(user_id=user_id, role_name=body.role_name),
        assigned_by=current_user.id,
    )
    return ok(message=f"Rol '{body.role_name}' asignado exitosamente")


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=StandardResponse[None],
)
async def remove_role(
    user_id: str,
    role_name: str,
    current_user: User = Depends(require_permission("roles:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Remover un rol de un usuario. Requiere roles:assign."""
    role_repo = SQLAlchemyRoleRepository(db)
    role = await role_repo.get_by_name(role_name)
    if role is None:
        raise NotFoundException(f"Rol '{role_name}' no encontrado")

    await role_repo.remove_role_from_user(
        user_id=user_id,
        role_id=role.id,
        removed_by=current_user.id,
    )
    permission_cache.invalidate(user_id)
    return ok(message=f"Rol '{role_name}' removido exitosamente")
