# Contributing to CAMIULA Backend

Guide for new developers joining the project (thesis teams, contributors).

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/LorenaFer/backendCAMIULA.git
cd backendCAMIULA
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 3. Apply migrations
alembic upgrade head

# 4. Start development server
make dev
# Or: uvicorn app.main:app --reload

# 5. View API docs
# Swagger: http://localhost:8000/docs
# ReDoc:   http://localhost:8000/redoc
# OpenAPI: http://localhost:8000/openapi.json
```

## Project Structure

```
backendCAMIULA/
    app/
        core/               # Config, security, exceptions
        shared/             # Database, middleware, schemas (shared across modules)
        modules/
            auth/           # Authentication + RBAC
            patients/       # Patient registry
            doctors/        # Doctors, specialties, availability
            appointments/   # Scheduling + state machine
            medical_records/ # Clinical records + form schemas
            inventory/      # Medications, suppliers, batches, dispatches
            dashboard/      # Cross-cutting BI aggregations
            reports/        # EPI epidemiological reports
    alembic/                # Database migrations
    tests/
        integration/        # HTTP endpoint tests (real DB)
        stress/             # Performance tests (100k+ records)
        unit/               # Unit tests
    scripts/                # Generators, seeders, validators
    docs/                   # Architecture, standards, API contracts
```

## Creating a New Module

```bash
# Generate the full scaffold
make new-module NAME=billing

# Or with specific entities
make new-module-entities NAME=laboratory ENTITIES=lab_order,lab_result
```

This creates:

```
app/modules/billing/
    router.py
    domain/
        entities/billing.py          # Pure dataclass
        repositories/billing_repository.py  # ABC interface
    application/
        dtos/billing_dto.py          # Data transfer objects
        use_cases/create_billing.py  # Business logic
        use_cases/list_billings.py
    infrastructure/
        models.py                    # SQLAlchemy model
        repositories/sqlalchemy_billing_repository.py
    presentation/
        dependencies.py              # DI factories (ONLY bridge to infra)
        routes/billing_router.py     # FastAPI endpoints
        schemas/billing_schemas.py   # Pydantic request/response
```

After generating, follow the printed instructions to register in alembic and main.py.

## Architecture Rules

### The Dependency Rule

```
presentation/ --> application/ --> domain/
                                     ^
infrastructure/ ─────────────────────┘
```

- **domain/** has zero external imports (no SQLAlchemy, no FastAPI)
- **application/** imports only from domain/ (use cases orchestrate via ABC repos)
- **infrastructure/** implements domain ABCs (SQLAlchemy, external APIs)
- **presentation/** talks to application/ via use cases, infra via dependencies.py ONLY

### Validate Before Committing

```bash
make validate          # Architecture rules
make validate-db       # Database standards
make test-integration  # All integration tests
```

## Coding Standards

### API Responses

Always use the response helpers from `app.shared.schemas.responses`:

```python
from app.shared.schemas.responses import ok, created, paginated

# GET endpoint
return ok(data=..., message="Retrieved successfully")

# POST endpoint (201)
return created(data=..., message="Created successfully")

# Paginated list
return paginated(items, total, page, page_size, "Items retrieved")
```

### Database Models

Follow the column order standard (docs/06-estandar-base-de-datos.md):

```python
class MyModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "my_table"

    # 1. Identity
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # 2. Foreign keys
    fk_parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("parents.id"))

    # 3. Domain fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 4. Business status
    my_status: Mapped[str] = mapped_column(String(20), default="active")

    # 5-8. status + audit (from mixins)
```

### Dependency Injection

Never import infrastructure in routers. Use the dependencies.py factory:

```python
# WRONG (architecture violation)
from app.modules.patients.infrastructure.repositories.sqlalchemy_patient_repository import SQLAlchemyPatientRepository
repo = SQLAlchemyPatientRepository(session)

# CORRECT
from app.modules.patients.presentation.dependencies import get_patient_repo
async def list_patients(repo: PatientRepository = Depends(get_patient_repo)):
```

### Error Handling

Use domain exceptions, never raw HTTPException:

```python
from app.core.exceptions import NotFoundException, ConflictException, AppException

raise NotFoundException("Patient not found")
raise ConflictException("Email already registered")
raise AppException("Custom error", status_code=400)
```

## Git Workflow

```
main ──────────── Production (stable)
  └── development ── QA/Testing
       └── feature/xxx ── Your feature branch
       └── fix/xxx ── Bug fix branch
       └── refactor/xxx ── Refactor branch
```

1. Branch from `development`
2. Make changes, run `make validate` and `make test`
3. Create PR against `development`
4. After QA approval, merge to `development`
5. Periodic releases merge `development` to `main`

### Commit Message Format

```
feat(module): short description
fix(module): what was fixed
refactor(module): what was refactored
test(module): what was tested
docs: what was documented
```

## Useful Commands

```bash
make help              # Show all available commands
make dev               # Start dev server
make test              # Run all tests
make test-module MODULE=patients  # Test one module
make validate          # Check architecture rules
make new-module NAME=x # Generate new module
make postman           # Export Postman collection
make migrate MSG="add_x_table"  # Create migration
make migrate-up        # Apply migrations
make seed              # Run all seeders
```

## Documentation

- Architecture: `docs/01-arquitectura.md`
- How to create a module: `docs/02-como-crear-un-modulo.md`
- API standards: `docs/05-estandar-respuestas-api.md`
- DB standards: `docs/06-estandar-base-de-datos.md`
- Performance rules: `docs/07-estandar-eficiencia.md`
- ADRs: `docs/08-architecture-decision-records.md`
- Dependency rule: `docs/10-dependency-rule.md`
- API endpoints: `docs/api/README.md`
