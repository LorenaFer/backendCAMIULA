# Cómo Crear un Nuevo Módulo

Guía paso a paso para desarrollar un módulo nuevo en el proyecto.

## Ejemplo: Crear el módulo `patients`

### Paso 1: Definir la Entidad (domain/entities/)

La entidad es un dataclass puro de Python. No depende de SQLAlchemy ni de FastAPI.

```python
# app/modules/patients/domain/entities/patient.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import uuid4

@dataclass
class Patient:
    first_name: str
    last_name: str
    cedula: str
    date_of_birth: date
    phone: str
    email: str = None
    id: str = field(default_factory=lambda: str(uuid4()))
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

### Paso 2: Definir el Contrato del Repositorio (domain/repositories/)

Interfaz abstracta que define QUÉ operaciones necesitas, sin decir CÓMO.

```python
# app/modules/patients/domain/repositories/patient_repository.py
from __future__ import annotations
from abc import ABC, abstractmethod
from app.modules.patients.domain.entities.patient import Patient

class PatientRepository(ABC):
    @abstractmethod
    async def create(self, patient: Patient) -> Patient:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, patient_id: str) -> Patient:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> list:
        raise NotImplementedError
```

### Paso 3: Crear los DTOs (application/dtos/)

Objetos que transportan datos entre capas.

```python
# app/modules/patients/application/dtos/patient_dto.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class CreatePatientDTO:
    first_name: str
    last_name: str
    cedula: str
    date_of_birth: date
    phone: str
    email: str = None
```

### Paso 4: Crear el Use Case (application/use_cases/)

Orquesta la lógica. Un use case = una acción del sistema.

```python
# app/modules/patients/application/use_cases/create_patient.py
from app.modules.patients.application.dtos.patient_dto import CreatePatientDTO
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository

class CreatePatientUseCase:
    def __init__(self, patient_repository: PatientRepository):
        self._repo = patient_repository

    async def execute(self, dto: CreatePatientDTO) -> Patient:
        patient = Patient(
            first_name=dto.first_name,
            last_name=dto.last_name,
            cedula=dto.cedula,
            date_of_birth=dto.date_of_birth,
            phone=dto.phone,
            email=dto.email,
        )
        return await self._repo.create(patient)
```

### Paso 5: Modelo SQLAlchemy (infrastructure/models.py)

**OBLIGATORIO:** Todo modelo DEBE heredar de `Base`, `SoftDeleteMixin` y `AuditMixin`, y seguir el [estándar de base de datos](./06-estandar-base-de-datos.md).

```python
# app/modules/patients/infrastructure/models.py
from typing import Optional

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin


class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"

    # --- Grupo 1: Identidad ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # --- Grupo 2: Relaciones (este modelo no tiene FKs) ---

    # --- Grupo 3: Dominio ---
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    date_of_birth: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Grupo 4: Lógica de negocio ---
    patient_status: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default=None
    )

    # --- Grupos 5-8: Vienen automáticamente de los mixins ---
    # status       → SoftDeleteMixin (A/I/T)
    # created_at   → AuditMixin
    # created_by   → AuditMixin
    # updated_at   → AuditMixin
    # updated_by   → AuditMixin
    # deleted_at   → AuditMixin
    # deleted_by   → AuditMixin
```

**IMPORTANTE para Python 3.9**: Usar `Optional[str]` en vez de `str | None`.

> **No definir** `is_active`, `created_at`, `status`, etc. manualmente — los mixins los proveen.

### Paso 6: Implementar el Repositorio (infrastructure/repositories/)

```python
# app/modules/patients/infrastructure/repositories/sqlalchemy_patient_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.patients.domain.entities.patient import Patient
from app.modules.patients.domain.repositories.patient_repository import PatientRepository
from app.modules.patients.infrastructure.models import PatientModel

class SQLAlchemyPatientRepository(PatientRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: PatientModel) -> Patient:
        return Patient(
            id=model.id,
            first_name=model.first_name,
            # ... mapear todos los campos
        )

    async def create(self, patient: Patient) -> Patient:
        model = PatientModel(id=patient.id, first_name=patient.first_name, ...)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)
```

### Paso 7: Schemas Pydantic (presentation/schemas/)

```python
# app/modules/patients/presentation/schemas/patient_schema.py
from datetime import date, datetime
from pydantic import BaseModel

class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    cedula: str
    date_of_birth: date
    phone: str

class PatientResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    cedula: str
    date_of_birth: date
    phone: str
    created_at: datetime
```

### Paso 8: Rutas FastAPI (presentation/routes/)

```python
# app/modules/patients/presentation/routes/patient_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database.session import get_db
from app.shared.middleware.auth import get_current_user_id

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    body: PatientCreateRequest,
    _: str = Depends(get_current_user_id),  # requiere autenticación
    db: AsyncSession = Depends(get_db),
):
    repo = SQLAlchemyPatientRepository(db)
    use_case = CreatePatientUseCase(repo)
    patient = await use_case.execute(CreatePatientDTO(...))
    return PatientResponse(...)
```

### Paso 9: Router del módulo

```python
# app/modules/patients/router.py
from fastapi import APIRouter
from app.modules.patients.presentation.routes.patient_routes import router as patient_router

router = APIRouter()
router.include_router(patient_router)
```

### Paso 10: Registrar en main.py

Agregar en `app/main.py`:

```python
from app.modules.patients.router import router as patients_router
app.include_router(patients_router, prefix="/api")
```

### Paso 11: Registrar modelo en Alembic y crear migración

Agregar en `alembic/env.py`:

```python
from app.modules.patients.infrastructure.models import PatientModel  # noqa: F401
```

Luego generar y aplicar la migración:

```bash
# 1. Generar migración automática
alembic revision --autogenerate -m "add patients table"

# 2. REVISAR la migración generada en alembic/versions/
#    Verificar: orden de columnas, constraints, downgrade
#    Ver checklist en docs/06-estandar-base-de-datos.md

# 3. Validar que el modelo cumple el estándar
python -c "
from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.validators import validate_column_order
v = validate_column_order(PatientModel)
print('OK' if not v else v)
"

# 4. Aplicar migración
alembic upgrade head
```

### Paso 12: Crear seeder (datos iniciales)

Si tu módulo necesita datos iniciales (roles, catálogos, usuarios admin, etc.),
crear un seeder en `infrastructure/seeders/`:

```python
# app/modules/patients/infrastructure/seeders/patient_seeder.py
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.infrastructure.models import PatientModel
from app.shared.database.seeder import BaseSeeder


class PatientSeeder(BaseSeeder):
    """Siembra pacientes de prueba para desarrollo."""

    order = 20  # Después del UserSeeder (order=10) si hay FKs

    async def run(self, session: AsyncSession) -> None:
        existing = await session.execute(
            select(PatientModel).where(PatientModel.cedula == "V-00000001")
        )
        if existing.scalar_one_or_none():
            return  # Ya existe, no duplicar

        test_patient = PatientModel(
            id=str(uuid4()),
            first_name="Paciente",
            last_name="De Prueba",
            cedula="V-00000001",
            phone="0414-0000000",
        )
        session.add(test_patient)

    async def clear(self, session: AsyncSession) -> None:
        await session.execute(
            delete(PatientModel).where(PatientModel.cedula == "V-00000001")
        )
```

Ejecutar seeders:

```bash
# Todos los seeders del proyecto
python -m app.shared.database.seeder

# Solo seeders de un módulo
python -m app.shared.database.seeder patients

# Limpiar y re-sembrar
python -m app.shared.database.seeder patients --fresh
```

### Resumen: Estructura final del módulo

```
app/modules/patients/
├── __init__.py
├── router.py                          ← Router principal
├── domain/
│   ├── entities/
│   │   └── patient.py                 ← Entidad pura (dataclass)
│   └── repositories/
│       └── patient_repository.py      ← Interfaz abstracta
├── application/
│   ├── dtos/
│   │   └── patient_dto.py             ← DTOs (transporte entre capas)
│   └── use_cases/
│       └── create_patient.py          ← Casos de uso
├── infrastructure/
│   ├── models.py                      ← Modelo SQLAlchemy (estándar de BD)
│   ├── repositories/
│   │   └── sqlalchemy_patient_repo.py ← Implementación del repositorio
│   └── seeders/
│       └── patient_seeder.py          ← Datos iniciales/de prueba
└── presentation/
    ├── routes/
    │   └── patient_routes.py          ← Endpoints FastAPI
    └── schemas/
        └── patient_schema.py          ← Schemas Pydantic (request/response)
```

Archivos centralizados que también hay que tocar:

| Archivo | Qué agregar |
|---------|-------------|
| `alembic/env.py` | Import del modelo (`PatientModel`) |
| `app/main.py` | `app.include_router(patients_router, prefix="/api")` |
