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

```python
# app/modules/patients/infrastructure/models.py
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database.base import Base

class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    date_of_birth: Mapped[datetime] = mapped_column(Date, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
```

**IMPORTANTE para Python 3.9**: En los modelos SQLAlchemy, usar `Optional[str]` en vez de `str | None`.

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

### Paso 11: Registrar modelo en Alembic

Agregar en `alembic/env.py`:

```python
from app.modules.patients.infrastructure.models import PatientModel  # noqa: F401
```

Luego crear migración:
```bash
alembic revision --autogenerate -m "add patients table"
alembic upgrade head
```
