# Clean Architecture - Explicación Simple

## El Problema que Resuelve

Sin arquitectura, todo el código queda mezclado: la lógica de negocio depende de la base de datos, los endpoints conocen detalles de SQL, y cambiar algo rompe todo lo demás.

Clean Architecture separa el código en **capas con responsabilidades claras**.

## Las 4 Capas

### 1. Domain (Dominio) - "Las reglas del negocio"

Es el corazón del sistema. Aquí vive:
- **Entidades**: objetos que representan conceptos del negocio (Paciente, Cita, etc.)
- **Repositorios (interfaces)**: contratos que dicen "necesito poder guardar/buscar pacientes", sin decir cómo
- **Servicios de dominio**: lógica de negocio que involucra varias entidades

```
¿Qué es un paciente? → Entidad
¿Qué puedo hacer con pacientes? → Interfaz del repositorio
¿Cómo se valida una cita? → Servicio de dominio
```

**Regla clave**: el dominio NO importa nada de las otras capas. Es Python puro.

### 2. Application (Aplicación) - "Los casos de uso"

Orquesta las operaciones. Cada archivo = una acción del sistema.

```
"Registrar un paciente" → CreatePatientUseCase
"Agendar una cita" → CreateAppointmentUseCase
"Listar inventario bajo" → ListLowStockUseCase
```

Usa las entidades del dominio y los contratos de repositorio, pero no sabe si la BD es PostgreSQL, MongoDB o un archivo JSON.

### 3. Infrastructure (Infraestructura) - "Los detalles técnicos"

Implementa los contratos del dominio con tecnología concreta:
- Modelos de SQLAlchemy (tablas de la BD)
- Repositorios concretos (las queries SQL reales)

```python
# El dominio dice: "necesito poder buscar paciente por cédula"
class PatientRepository(ABC):
    async def get_by_cedula(self, cedula: str) -> Patient: ...

# La infraestructura dice: "yo lo hago con SQLAlchemy"
class SQLAlchemyPatientRepository(PatientRepository):
    async def get_by_cedula(self, cedula: str) -> Patient:
        stmt = select(PatientModel).where(PatientModel.cedula == cedula)
        ...
```

### 4. Presentation (Presentación) - "La interfaz HTTP"

Lo que ve el mundo exterior:
- **Routes**: endpoints de FastAPI (`POST /api/patients`)
- **Schemas**: validación de request/response con Pydantic

Esta capa recibe HTTP, lo traduce a DTOs, ejecuta use cases, y devuelve respuestas JSON.

## Flujo de una Request

```
Cliente HTTP
    │
    ▼
[Presentation] POST /api/patients
    │  Valida request con Pydantic schema
    │  Crea DTO
    ▼
[Application] CreatePatientUseCase.execute(dto)
    │  Crea entidad de dominio
    │  Llama al repositorio
    ▼
[Domain] Patient entity + PatientRepository interface
    │
    ▼
[Infrastructure] SQLAlchemyPatientRepository.create(patient)
    │  INSERT INTO patients ...
    ▼
PostgreSQL
```

## Analogía Simple

Piensa en un restaurante:

| Capa | Restaurante |
|------|-------------|
| **Presentation** | El mesero: toma tu pedido y te trae la comida |
| **Application** | El chef de cocina: coordina la preparación |
| **Domain** | Las recetas: las reglas de cómo se prepara cada plato |
| **Infrastructure** | La cocina y sus herramientas: horno, nevera, sartenes |

Puedes cambiar el horno (infraestructura) sin cambiar las recetas (dominio). Puedes cambiar el mesero (presentación) sin cambiar al chef (aplicación).
