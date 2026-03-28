from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.seeder import BaseSeeder


class PatientSeeder(BaseSeeder):
    """Siembra pacientes de prueba para desarrollo."""

    order = 20

    async def run(self, session: AsyncSession) -> None:
        existing = await session.execute(
            select(PatientModel).where(PatientModel.cedula == "V-12345678")
        )
        if existing.scalar_one_or_none():
            return

        # Obtener NHMs de la secuencia
        nhm1 = (await session.execute(text("SELECT nextval('nhm_seq')"))).scalar_one()
        nhm2 = (await session.execute(text("SELECT nextval('nhm_seq')"))).scalar_one()

        patients = [
            PatientModel(
                id=str(uuid4()),
                nhm=nhm1,
                cedula="V-12345678",
                first_name="Maria",
                last_name="Garcia",
                sex="F",
                university_relation="empleado",
                phone="0414-1234567",
                medical_data={
                    "tipo_sangre": "O+",
                    "alergias": ["Penicilina"],
                    "numero_contacto": "0414-1234567",
                    "condiciones": [],
                },
                emergency_contact={
                    "nombre": "Juan Garcia",
                    "parentesco": "esposo",
                    "direccion": "Av. Los Proceres, Merida",
                    "telefono": "0414-7654321",
                },
                is_new=False,
            ),
            PatientModel(
                id=str(uuid4()),
                nhm=nhm2,
                cedula="V-87654321",
                first_name="Pedro",
                last_name="Lopez",
                sex="M",
                university_relation="profesor",
                phone="0412-9876543",
                is_new=True,
            ),
        ]
        session.add_all(patients)

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        await session.execute(
            delete(PatientModel).where(
                PatientModel.cedula.in_(["V-12345678", "V-87654321"])
            )
        )
