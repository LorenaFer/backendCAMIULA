from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.infrastructure.models import SpecialtyModel
from app.shared.database.seeder import BaseSeeder

SPECIALTIES = [
    "Medicina General",
    "Pediatría",
    "Ginecología",
    "Traumatología",
    "Odontología",
    "Oftalmología",
    "Dermatología",
    "Cardiología",
    "Psicología",
    "Nutrición",
]


class SpecialtySeeder(BaseSeeder):
    """Siembra especialidades médicas. Idempotente por nombre."""

    order = 15

    async def run(self, session: AsyncSession) -> None:
        for name in SPECIALTIES:
            existing = await session.execute(
                select(SpecialtyModel).where(SpecialtyModel.name == name)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(SpecialtyModel(id=str(uuid4()), name=name))

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        await session.execute(
            delete(SpecialtyModel).where(SpecialtyModel.name.in_(SPECIALTIES))
        )
