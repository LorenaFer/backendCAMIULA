"""TDD — Specialty CRUD: POST, PUT, PATCH toggle.

Probamos las use cases con repositorios mock.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────

def make_specialty(id="sp-1", name="Cardiología", is_active=True):
    from app.modules.appointments.domain.entities.specialty import Specialty
    return Specialty(id=id, name=name, is_active=is_active)


# ──────────────────────────────────────────────────────────────────────────────
# CreateSpecialtyUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateSpecialtyUseCase:
    @pytest.mark.asyncio
    async def test_creates_and_returns_specialty(self):
        from app.modules.appointments.application.use_cases.create_specialty import (
            CreateSpecialtyUseCase,
        )
        repo = MagicMock()
        new_sp = make_specialty(name="Cardiología")
        repo.create = AsyncMock(return_value=new_sp)
        repo.get_by_name = AsyncMock(return_value=None)

        uc = CreateSpecialtyUseCase(specialty_repo=repo)
        result = await uc.execute("Cardiología", created_by="user-1")

        assert result.name == "Cardiología"
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_if_name_already_exists(self):
        from app.modules.appointments.application.use_cases.create_specialty import (
            CreateSpecialtyUseCase,
        )
        from app.core.exceptions import AppException

        repo = MagicMock()
        repo.get_by_name = AsyncMock(return_value=make_specialty(name="Cardiología"))

        uc = CreateSpecialtyUseCase(specialty_repo=repo)
        with pytest.raises(AppException):
            await uc.execute("Cardiología", created_by="user-1")


# ──────────────────────────────────────────────────────────────────────────────
# UpdateSpecialtyUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestUpdateSpecialtyUseCase:
    @pytest.mark.asyncio
    async def test_updates_name(self):
        from app.modules.appointments.application.use_cases.update_specialty import (
            UpdateSpecialtyUseCase,
        )
        repo = MagicMock()
        updated = make_specialty(name="Cardiología Intervencionista")
        repo.get_by_id = AsyncMock(return_value=make_specialty())
        repo.get_by_name = AsyncMock(return_value=None)
        repo.update = AsyncMock(return_value=updated)

        uc = UpdateSpecialtyUseCase(specialty_repo=repo)
        result = await uc.execute("sp-1", "Cardiología Intervencionista", updated_by="user-1")

        assert result.name == "Cardiología Intervencionista"
        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_if_not_found(self):
        from app.modules.appointments.application.use_cases.update_specialty import (
            UpdateSpecialtyUseCase,
        )
        from app.core.exceptions import AppException

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)

        uc = UpdateSpecialtyUseCase(specialty_repo=repo)
        with pytest.raises(AppException):
            await uc.execute("sp-999", "Nuevo Nombre", updated_by="user-1")


# ──────────────────────────────────────────────────────────────────────────────
# ToggleSpecialtyUseCase
# ──────────────────────────────────────────────────────────────────────────────

class TestToggleSpecialtyUseCase:
    @pytest.mark.asyncio
    async def test_toggles_active_to_inactive(self):
        from app.modules.appointments.application.use_cases.toggle_specialty import (
            ToggleSpecialtyUseCase,
        )
        repo = MagicMock()
        toggled = make_specialty(is_active=False)
        repo.get_by_id = AsyncMock(return_value=make_specialty(is_active=True))
        repo.toggle = AsyncMock(return_value=toggled)

        uc = ToggleSpecialtyUseCase(specialty_repo=repo)
        result = await uc.execute("sp-1", updated_by="user-1")

        assert result.is_active is False
        repo.toggle.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_if_not_found(self):
        from app.modules.appointments.application.use_cases.toggle_specialty import (
            ToggleSpecialtyUseCase,
        )
        from app.core.exceptions import AppException

        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)

        uc = ToggleSpecialtyUseCase(specialty_repo=repo)
        with pytest.raises(AppException):
            await uc.execute("sp-999", updated_by="user-1")
