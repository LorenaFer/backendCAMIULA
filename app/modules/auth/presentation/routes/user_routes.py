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
from app.modules.auth.application.dtos.auth_dto import RegisterDTO
from app.modules.auth.application.use_cases.register_user import RegisterUserUseCase
from app.modules.auth.presentation.schemas.auth_schema import (
    AssignRoleRequest,
    CreateUserRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.shared.database.session import get_db
from app.shared.middleware.auth import (
    get_current_user,
    require_permission,
)
from app.shared.middleware.permission_cache import permission_cache
from app.shared.schemas.common import PaginatedData, StandardResponse
from app.shared.schemas.responses import created, ok, paginated

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


@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_my_profile(
    user: User = Depends(require_permission("profile:read")),
):
    """Obtener perfil del usuario autenticado."""
    return ok(data=_to_response(user), message="Perfil obtenido")


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
    search: str = Query(None, description="Search by email or name"),
    role: str = Query(None, description="Filter by role name"),
    staff_only: bool = Query(False, description="Exclude users whose only role is paciente"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination, search and role filters."""
    repo = SQLAlchemyUserRepository(db)
    users, total = await repo.list_paginated(
        page,
        page_size,
        search=search,
        role=role,
        exclude_only_role="paciente" if staff_only else None,
    )

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


@router.post("", status_code=201, response_model=StandardResponse[UserResponse])
async def create_user(
    body: CreateUserRequest,
    current_user: User = Depends(require_permission("users:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a staff user with roles. Requires users:create."""
    user_repo = SQLAlchemyUserRepository(db)
    role_repo = SQLAlchemyRoleRepository(db)

    # Register the user (assigns 'paciente' by default)
    use_case = RegisterUserUseCase(user_repo=user_repo, role_repo=role_repo)
    user = await use_case.execute(
        RegisterDTO(
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            phone=body.phone,
        )
    )

    # Assign additional roles
    assign_uc = AssignRoleUseCase(
        user_repo=user_repo,
        role_repo=role_repo,
        permission_cache=permission_cache,
    )
    for role_name in body.roles:
        if role_name != "paciente":  # paciente already assigned by register
            try:
                await assign_uc.execute(
                    dto=AssignRoleDTO(user_id=user.id, role_name=role_name),
                    assigned_by=current_user.id,
                )
            except Exception:
                pass  # Role might not exist or already assigned

    # Reload roles
    user.roles = await user_repo.get_user_roles(user.id)

    return created(
        data=_to_response(user),
        message="Usuario creado exitosamente",
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
