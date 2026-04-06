# The Dependency Rule

## Diagram

```
                    ┌─────────────────────────────┐
                    │      presentation/           │
                    │   routes/ + schemas/         │
                    │                              │
                    │   dependencies.py ──────┐    │
                    └──────────┬──────────────┼────┘
                               │              │
                    ┌──────────▼──────────┐   │
                    │    application/      │   │
                    │   use_cases/ + dtos/ │   │
                    └──────────┬──────────┘   │
                               │              │
                    ┌──────────▼──────────┐   │
                    │      domain/        │   │
                    │ entities/ + repos/  │   │
                    │    (ABC interfaces) │   │
                    └─────────────────────┘   │
                                              │
                    ┌─────────────────────────▼────┐
                    │     infrastructure/           │
                    │  models.py + sqlalchemy_repos │
                    │  (implements domain ABCs)     │
                    └──────────────────────────────┘
```

## Rules

| Layer | Can import from | CANNOT import from |
|-------|----------------|--------------------|
| `domain/` | `shared/` only | application, infrastructure, presentation, sqlalchemy |
| `application/` | `domain/`, `shared/` | infrastructure, presentation, sqlalchemy |
| `infrastructure/` | `domain/`, `shared/` | application, presentation |
| `presentation/routes/` | `application/`, `shared/`, own `dependencies.py` | infrastructure (directly) |
| `presentation/dependencies.py` | `domain/`, `infrastructure/`, `shared/` | This is the ONLY bridge |

## Correct Pattern

```python
# presentation/dependencies.py (THE bridge)
from app.modules.patients.domain.repositories.patient_repository import PatientRepository
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import SQLAlchemyPatientRepository

def get_patient_repo(session=Depends(get_db)) -> PatientRepository:
    return SQLAlchemyPatientRepository(session)
```

```python
# presentation/routes/patients_router.py (CLEAN)
from app.modules.patients.presentation.dependencies import get_patient_repo

@router.get("")
async def list_patients(repo: PatientRepository = Depends(get_patient_repo)):
    ...
```

## Violation Examples

```python
# BAD: Router imports concrete repo
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import SQLAlchemyPatientRepository

# BAD: Use case imports SQLAlchemy
from sqlalchemy import select

# BAD: Domain imports infrastructure model
from app.modules.patients.infrastructure.models import PatientModel
```

## Validation

Run the architecture validator:
```bash
python scripts/validate_architecture.py              # Full scan
python scripts/validate_architecture.py --module patients  # Single module
python scripts/validate_architecture.py --git-diff HEAD~1  # Only changed files
```
