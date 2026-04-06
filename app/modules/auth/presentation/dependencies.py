"""Dependency injection factories for the Auth module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.domain.repositories.user_repository import UserRepository
from app.modules.auth.infrastructure.repositories.sqlalchemy_role_repository import (
    SQLAlchemyRoleRepository,
)
from app.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.shared.database.session import get_db


def get_user_repo(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_role_repo(
    session: AsyncSession = Depends(get_db),
) -> RoleRepository:
    return SQLAlchemyRoleRepository(session)
