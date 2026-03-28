from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.domain.entities.enums import DoctorStatus
from app.modules.appointments.infrastructure.models import DoctorModel, SpecialtyModel
from app.modules.auth.infrastructure.models import UserModel
from app.shared.database.seeder import BaseSeeder


class DoctorSeeder(BaseSeeder):
    """Siembra perfiles de doctor para usuarios con rol doctor. Idempotente."""

    order = 25

    async def run(self, session: AsyncSession) -> None:
        # Buscar el usuario doctor del seeder de auth
        result = await session.execute(
            select(UserModel).where(UserModel.email == "doctor@camiula.com")
        )
        doctor_user = result.scalar_one_or_none()
        if doctor_user is None:
            return

        # Verificar si ya tiene perfil
        existing = await session.execute(
            select(DoctorModel).where(DoctorModel.fk_user_id == doctor_user.id)
        )
        if existing.scalar_one_or_none():
            return

        # Obtener especialidad Medicina General
        spec_result = await session.execute(
            select(SpecialtyModel).where(SpecialtyModel.name == "Medicina General")
        )
        specialty = spec_result.scalar_one_or_none()
        if specialty is None:
            return

        session.add(
            DoctorModel(
                id=str(uuid4()),
                fk_user_id=doctor_user.id,
                fk_specialty_id=specialty.id,
                first_name="Carlos",
                last_name="Mendoza",
                doctor_status=DoctorStatus.ACTIVE.value,
            )
        )

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        await session.execute(
            delete(DoctorModel).where(DoctorModel.first_name == "Carlos")
        )
