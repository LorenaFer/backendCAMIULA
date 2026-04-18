"""Repositorio simple para la tabla revoked_tokens.

No sigue el patrón domain/infrastructure porque es una utilidad cross-cutting
del sistema de auth — un log de revocaciones sin lógica de dominio.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import RevokedTokenModel


class RevokedTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        stmt = select(RevokedTokenModel.jti).where(RevokedTokenModel.jti == jti)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def revoke(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
        token_type: str,
    ) -> None:
        # Idempotente: si ya está revocado no hace nada.
        existing = await self.is_revoked(jti)
        if existing:
            return
        self._db.add(
            RevokedTokenModel(
                jti=jti,
                fk_user_id=user_id,
                expires_at=expires_at,
                token_type=token_type,
            )
        )
        await self._db.commit()
