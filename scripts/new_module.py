#!/usr/bin/env python3
"""Generate a new Clean Architecture module scaffold.

Usage:
    python scripts/new_module.py <module_name>
    python scripts/new_module.py <module_name> --entities entity1,entity2

Examples:
    python scripts/new_module.py billing
    python scripts/new_module.py laboratory --entities lab_order,lab_result

Creates the full directory structure with boilerplate files following
the CAMIULA architecture standards (see docs/10-dependency-rule.md).
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "app" / "modules"


def snake_to_pascal(s: str) -> str:
    return "".join(w.capitalize() for w in s.split("_"))


def create_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"  SKIP  {path.relative_to(ROOT)} (already exists)")
        return
    path.write_text(content)
    print(f"  CREATE {path.relative_to(ROOT)}")


def generate_module(module_name: str, entities: list):
    mod = MODULES / module_name
    entity = entities[0] if entities else module_name
    Entity = snake_to_pascal(entity)
    Module = snake_to_pascal(module_name)

    print(f"\nGenerating module: {module_name}")
    print(f"  Entity: {entity} ({Entity})")
    print(f"  Path: app/modules/{module_name}/\n")

    # ── __init__.py files ────────────────────────────────
    for sub in [
        "",
        "domain", "domain/entities", "domain/repositories",
        "application", "application/dtos", "application/use_cases",
        "infrastructure", "infrastructure/repositories", "infrastructure/seeders",
        "presentation", "presentation/routes", "presentation/schemas",
    ]:
        create_file(mod / sub / "__init__.py" if sub else mod / "__init__.py", "")

    # ── domain/entities/{entity}.py ──────────────────────
    create_file(
        mod / "domain" / "entities" / f"{entity}.py",
        f'''"""Domain entity: {Entity}."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class {Entity}:
    id: str
    # TODO: add domain fields
    created_at: Optional[str] = None
    created_by: Optional[str] = None
''',
    )

    # ── domain/repositories/{entity}_repository.py ───────
    create_file(
        mod / "domain" / "repositories" / f"{entity}_repository.py",
        f'''"""Abstract interface for the {Entity} repository."""

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.{module_name}.domain.entities.{entity} import {Entity}


class {Entity}Repository(ABC):

    @abstractmethod
    async def find_all(
        self, search: Optional[str], page: int, page_size: int
    ) -> tuple[list[{Entity}], int]:
        """Return (items, total) for pagination."""
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[{Entity}]:
        ...

    @abstractmethod
    async def create(self, data: dict, created_by: str) -> {Entity}:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict, updated_by: str) -> Optional[{Entity}]:
        ...

    @abstractmethod
    async def soft_delete(self, id: str, deleted_by: str) -> bool:
        ...
''',
    )

    # ── application/dtos/{entity}_dto.py ─────────────────
    create_file(
        mod / "application" / "dtos" / f"{entity}_dto.py",
        f'''"""DTOs for {Entity} use cases."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Create{Entity}DTO:
    # TODO: add fields
    pass


@dataclass
class Update{Entity}DTO:
    # TODO: add fields
    pass
''',
    )

    # ── application/use_cases/create_{entity}.py ─────────
    create_file(
        mod / "application" / "use_cases" / f"create_{entity}.py",
        f'''"""Use case: Create {Entity}."""

from app.modules.{module_name}.application.dtos.{entity}_dto import Create{Entity}DTO
from app.modules.{module_name}.domain.entities.{entity} import {Entity}
from app.modules.{module_name}.domain.repositories.{entity}_repository import (
    {Entity}Repository,
)


class Create{Entity}:

    def __init__(self, repo: {Entity}Repository) -> None:
        self._repo = repo

    async def execute(self, dto: Create{Entity}DTO, created_by: str) -> {Entity}:
        data = {{
            # TODO: map DTO fields to dict
        }}
        return await self._repo.create(data, created_by)
''',
    )

    # ── application/use_cases/list_{entity}s.py ──────────
    create_file(
        mod / "application" / "use_cases" / f"list_{entity}s.py",
        f'''"""Use case: List {Entity}s with pagination."""

from typing import Optional

from app.modules.{module_name}.domain.entities.{entity} import {Entity}
from app.modules.{module_name}.domain.repositories.{entity}_repository import (
    {Entity}Repository,
)


class List{Entity}s:

    def __init__(self, repo: {Entity}Repository) -> None:
        self._repo = repo

    async def execute(
        self, search: Optional[str], page: int, page_size: int
    ) -> tuple[list[{Entity}], int]:
        return await self._repo.find_all(search=search, page=page, page_size=page_size)
''',
    )

    # ── infrastructure/models.py ─────────────────────────
    create_file(
        mod / "infrastructure" / "models.py",
        f'''"""SQLAlchemy models for the {Module} module.

Column order standard: id -> fk_* -> domain -> table_status -> status -> audit
See: docs/06-estandar-base-de-datos.md
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class {Entity}Model(Base, SoftDeleteMixin, AuditMixin):
    """{Entity} database model."""

    __tablename__ = "{entity}s"

    # 1. Identity
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4()),
    )

    # 2. Foreign keys (fk_*)
    # TODO: add FKs

    # 3. Domain fields
    # TODO: add domain columns

    # 4. Business status
    # {entity}_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # 5-8. status + audit -> provided by mixins
''',
    )

    # ── infrastructure/repositories/sqlalchemy_{entity}_repository.py
    create_file(
        mod / "infrastructure" / "repositories" / f"sqlalchemy_{entity}_repository.py",
        f'''"""SQLAlchemy implementation of {Entity}Repository."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import func, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.{module_name}.domain.entities.{entity} import {Entity}
from app.modules.{module_name}.domain.repositories.{entity}_repository import (
    {Entity}Repository,
)
from app.modules.{module_name}.infrastructure.models import {Entity}Model
from app.shared.database.mixins import RecordStatus


class SQLAlchemy{Entity}Repository({Entity}Repository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_entity(model: {Entity}Model) -> {Entity}:
        return {Entity}(
            id=model.id,
            # TODO: map model fields to entity
            created_at=model.created_at.isoformat() if model.created_at else None,
            created_by=model.created_by,
        )

    async def find_all(
        self, search: Optional[str], page: int, page_size: int
    ) -> tuple[list[{Entity}], int]:
        q = select({Entity}Model).where({Entity}Model.status == RecordStatus.ACTIVE)
        # TODO: add search filters

        total = (
            await self._session.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()

        offset = (page - 1) * page_size
        result = await self._session.execute(q.offset(offset).limit(page_size))
        return [self._to_entity(m) for m in result.scalars().all()], total

    async def find_by_id(self, id: str) -> Optional[{Entity}]:
        result = await self._session.execute(
            select({Entity}Model).where(
                {Entity}Model.id == id,
                {Entity}Model.status == RecordStatus.ACTIVE,
            )
        )
        m = result.scalar_one_or_none()
        return self._to_entity(m) if m else None

    async def create(self, data: dict, created_by: str) -> {Entity}:
        model = {Entity}Model(id=str(uuid4()), created_by=created_by, **data)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, id: str, data: dict, updated_by: str) -> Optional[{Entity}]:
        data["updated_at"] = datetime.now(timezone.utc)
        data["updated_by"] = updated_by
        await self._session.execute(
            sql_update({Entity}Model).where({Entity}Model.id == id).values(**data)
        )
        await self._session.flush()
        return await self.find_by_id(id)

    async def soft_delete(self, id: str, deleted_by: str) -> bool:
        result = await self._session.execute(
            sql_update({Entity}Model)
            .where({Entity}Model.id == id, {Entity}Model.status == RecordStatus.ACTIVE)
            .values(
                status=RecordStatus.TRASH,
                deleted_at=datetime.now(timezone.utc),
                deleted_by=deleted_by,
            )
        )
        return result.rowcount > 0
''',
    )

    # ── presentation/dependencies.py ─────────────────────
    create_file(
        mod / "presentation" / "dependencies.py",
        f'''"""Dependency injection factories for the {Module} module.

This is the ONLY presentation file allowed to import from infrastructure.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.{module_name}.domain.repositories.{entity}_repository import (
    {Entity}Repository,
)
from app.modules.{module_name}.infrastructure.repositories.sqlalchemy_{entity}_repository import (
    SQLAlchemy{Entity}Repository,
)
from app.shared.database.session import get_db


def get_{entity}_repo(
    session: AsyncSession = Depends(get_db),
) -> {Entity}Repository:
    return SQLAlchemy{Entity}Repository(session)
''',
    )

    # ── presentation/schemas/{entity}_schemas.py ─────────
    create_file(
        mod / "presentation" / "schemas" / f"{entity}_schemas.py",
        f'''"""Pydantic schemas for {Entity} request/response."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class {Entity}Create(BaseModel):
    # TODO: add create fields
    pass


class {Entity}Update(BaseModel):
    # TODO: add update fields
    pass


class {Entity}Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    # TODO: add response fields
    created_at: Optional[str] = None
''',
    )

    # ── presentation/routes/{entity}_router.py ───────────
    create_file(
        mod / "presentation" / "routes" / f"{entity}_router.py",
        f'''"""FastAPI routes for the {Entity} resource."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.modules.{module_name}.domain.repositories.{entity}_repository import (
    {Entity}Repository,
)
from app.modules.{module_name}.presentation.dependencies import get_{entity}_repo
from app.modules.{module_name}.presentation.schemas.{entity}_schemas import (
    {Entity}Create,
    {Entity}Response,
    {Entity}Update,
)
from app.shared.middleware.auth import get_current_user_id, get_optional_user_id
from app.shared.schemas.responses import created, ok, paginated

router = APIRouter(prefix="/{entity}s", tags=["{Module}"])


@router.get("", summary="List {entity}s (paginated)")
async def list_{entity}s(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: {Entity}Repository = Depends(get_{entity}_repo),
    user_id: str = Depends(get_optional_user_id),
):
    items, total = await repo.find_all(search=search, page=page, page_size=page_size)
    data = [{Entity}Response(**i.__dict__) for i in items]
    return paginated(data, total, page, page_size, "{Entity}s retrieved")


@router.get("/{{id}}", summary="Get {entity} by ID")
async def get_{entity}(
    id: str,
    repo: {Entity}Repository = Depends(get_{entity}_repo),
    user_id: str = Depends(get_optional_user_id),
):
    entity = await repo.find_by_id(id)
    if not entity:
        raise NotFoundException("{Entity} not found")
    return ok(data={Entity}Response(**entity.__dict__), message="{Entity} retrieved")


@router.post("", summary="Create {entity}", status_code=201)
async def create_{entity}(
    body: {Entity}Create,
    repo: {Entity}Repository = Depends(get_{entity}_repo),
    user_id: str = Depends(get_current_user_id),
):
    entity = await repo.create(data=body.model_dump(), created_by=user_id)
    return created(data={Entity}Response(**entity.__dict__), message="{Entity} created")


@router.patch("/{{id}}", summary="Update {entity}")
async def update_{entity}(
    id: str,
    body: {Entity}Update,
    repo: {Entity}Repository = Depends(get_{entity}_repo),
    user_id: str = Depends(get_current_user_id),
):
    entity = await repo.update(id=id, data=body.model_dump(exclude_none=True), updated_by=user_id)
    if not entity:
        raise NotFoundException("{Entity} not found")
    return ok(data={Entity}Response(**entity.__dict__), message="{Entity} updated")


@router.delete("/{{id}}", summary="Delete {entity} (soft-delete)")
async def delete_{entity}(
    id: str,
    repo: {Entity}Repository = Depends(get_{entity}_repo),
    user_id: str = Depends(get_current_user_id),
):
    deleted = await repo.soft_delete(id=id, deleted_by=user_id)
    if not deleted:
        raise NotFoundException("{Entity} not found")
    return ok(message="{Entity} deleted")
''',
    )

    # ── router.py (module aggregator) ────────────────────
    create_file(
        mod / "router.py",
        f'''"""Router for the {Module} module."""

from fastapi import APIRouter

from app.modules.{module_name}.presentation.routes.{entity}_router import (
    router as {entity}_router,
)

router = APIRouter()
router.include_router({entity}_router)
''',
    )

    # ── Summary ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Module '{module_name}' created successfully!")
    print(f"{'='*60}")
    print(f"""
Next steps:
  1. Edit the model:     app/modules/{module_name}/infrastructure/models.py
  2. Edit the entity:    app/modules/{module_name}/domain/entities/{entity}.py
  3. Edit the schemas:   app/modules/{module_name}/presentation/schemas/{entity}_schemas.py
  4. Edit the DTOs:      app/modules/{module_name}/application/dtos/{entity}_dto.py
  5. Register in alembic: alembic/env.py (import {Entity}Model)
  6. Register in main:    app/main.py (include_router)
  7. Create migration:    alembic revision --autogenerate -m "add_{entity}s_table"
  8. Apply migration:     alembic upgrade head
  9. Run validator:       python scripts/validate_architecture.py --module {module_name}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new Clean Architecture module scaffold",
        epilog="Example: python scripts/new_module.py billing --entities invoice,payment",
    )
    parser.add_argument("module_name", help="Module name (snake_case)")
    parser.add_argument(
        "--entities", default=None,
        help="Comma-separated entity names (default: same as module_name)",
    )
    args = parser.parse_args()

    module_name = args.module_name.lower().replace("-", "_")
    entities = (
        [e.strip() for e in args.entities.split(",")]
        if args.entities
        else [module_name]
    )

    if (MODULES / module_name).exists():
        print(f"Warning: module '{module_name}' already exists. Only missing files will be created.")

    generate_module(module_name, entities)


if __name__ == "__main__":
    main()
