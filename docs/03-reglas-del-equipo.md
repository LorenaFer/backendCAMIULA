# Reglas del Equipo

## Asignación de Módulos

Cada dev es responsable de su módulo. Esto minimiza conflictos de merge.

| Módulo | Ruta API | Descripción |
|--------|----------|-------------|
| `auth` | `/api/auth`, `/api/users` | Registro, login, gestión de usuarios |
| `patients` | `/api/patients` | CRUD de pacientes |
| `appointments` | `/api/appointments` | Gestión de citas médicas |
| `inventory` | `/api/inventory` | Control de inventario de insumos |

## Reglas de Código

### 1. Formato estándar de respuestas API

**Obligatorio.** Todo endpoint DEBE usar los helpers de `app.shared.schemas.responses`:

```python
from app.shared.schemas.responses import ok, created, error, paginated

# Éxito
return ok(data=patient.model_dump(), message="Paciente obtenido")

# Creación
return created(data=new.model_dump(), message="Paciente creado")

# Paginación
return paginated(items=[...], total=45, page=1, page_size=20)

# Errores → usar excepciones
raise NotFoundException("Paciente no encontrado")
```

**Prohibido:** `JSONResponse(...)` directo, `return {"success": ...}`, `raise HTTPException(...)`.

Ver documentación completa: [05-estandar-respuestas-api.md](./05-estandar-respuestas-api.md)

### 2. Estándar de base de datos

**Obligatorio.** Todo modelo SQLAlchemy DEBE:

- Heredar de `Base`, `SoftDeleteMixin` y `AuditMixin`
- Seguir el orden de columnas: `id → fk_* → datos → table_status → (mixins)`
- Usar `fk_` como prefijo en foreign keys
- **Nunca** definir `created_at`, `status`, etc. manualmente (los mixins los proveen)
- **Nunca** hacer `DELETE FROM` — usar soft-delete con `status = 'T'`

```python
from app.shared.database.base import Base
from app.shared.database.mixins import AuditMixin, SoftDeleteMixin

class PatientModel(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # ... datos del dominio ...
    # status, created_at, created_by, etc. vienen de los mixins
```

Ver documentación completa: [06-estandar-base-de-datos.md](./06-estandar-base-de-datos.md)

### 3. Eficiencia y complejidad algorítmica

**Obligatorio.** Todo código DEBE cumplir los estándares de eficiencia. Los jurados evaluarán Big O.

**Prohibido:**
- N+1 queries (loop + query → usar `selectinload`/`joinedload`)
- Listados sin paginación (`page_size` máximo 100)
- `len(.all())` para contar (usar `func.count()`)
- Filtrar en Python lo que se puede filtrar con WHERE en SQL
- `flush()` dentro de loops (usar `add_all()`)
- Operaciones bloqueantes (`time.sleep`, `requests.get` sync)

```python
# Siempre paginado, siempre con índice, siempre en BD
stmt = (
    select(PatientModel.id, PatientModel.first_name, PatientModel.cedula)
    .where(PatientModel.status == RecordStatus.ACTIVE)
    .order_by(PatientModel.created_at.desc())
    .offset((page - 1) * page_size)
    .limit(page_size)
)
```

Ver documentación completa: [07-estandar-eficiencia.md](./07-estandar-eficiencia.md)

### 4. No importar entre módulos
```python
# MAL - crea acoplamiento
from app.modules.auth.domain.entities.user import User  # desde el módulo patients

# BIEN - si necesitas algo compartido, ponlo en shared/
from app.shared.schemas.common import MessageResponse
```

### 5. Coordinar cambios en zonas compartidas
Estos archivos afectan a todos. Avisar al equipo antes de modificar:
- `app/core/*`
- `app/shared/*`
- `app/main.py`
- `alembic/env.py`
- `requirements.txt`

### 6. Migraciones de BD
- **NUNCA** editar una migración que ya se hizo push
- Coordinar antes de crear migraciones nuevas (pueden haber conflictos en Alembic)
- Nombrar las migraciones descriptivamente: `alembic revision --autogenerate -m "add patients table"`

### 7. Branching
```bash
# Crear rama desde main
git checkout main
git pull origin main
git checkout -b feature/patients-crud

# Trabajar, commitear
git add .
git commit -m "feat(patients): add CRUD endpoints"

# Push y PR
git push -u origin feature/patients-crud
# Crear PR en GitHub
```

### 8. Convención de commits
```
feat(modulo): descripción      ← nueva funcionalidad
fix(modulo): descripción       ← corrección de bug
refactor(modulo): descripción  ← cambio interno sin cambiar comportamiento
docs: descripción              ← documentación
```

Ejemplos:
```
feat(auth): add login endpoint with JWT
fix(patients): handle duplicate cedula correctly
refactor(inventory): extract repository to separate file
docs: add module creation guide
```

## Setup del proyecto

```bash
# 1. Clonar
git clone https://github.com/LorenaFer/backendCAMIULA.git
cd backendCAMIULA

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables
cp .env.example .env
# Editar .env con las credenciales de tu BD local

# 5. Correr migraciones (cuando haya)
alembic upgrade head

# 6. Iniciar servidor
uvicorn app.main:app --reload

# 7. Ver docs de la API
# Abrir http://localhost:8000/docs
```

## Tests

```bash
# Correr todos los tests
pytest

# Correr tests de un módulo
pytest tests/unit/test_patients.py -v
```
