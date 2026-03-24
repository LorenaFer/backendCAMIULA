# CAMIULA Backend API

Backend API para el sistema CAMIULA construido con FastAPI y arquitectura de monolito modular.

## Documentación

Ver la carpeta `docs/` para guías detalladas:

- [01 - Arquitectura del proyecto](docs/01-arquitectura.md)
- [02 - Cómo crear un módulo](docs/02-como-crear-un-modulo.md)
- [03 - Reglas del equipo](docs/03-reglas-del-equipo.md)
- [04 - Clean Architecture explicada](docs/04-clean-architecture-explicada.md)

## Estructura

```
app/
├── core/              # Configuración, seguridad, excepciones
├── shared/            # Código compartido (DB, middleware, schemas)
└── modules/           # Módulos de negocio
    ├── auth/          # Autenticación y usuarios
    ├── patients/      # Gestión de pacientes
    ├── appointments/  # Gestión de citas
    └── inventory/     # Control de inventario
```

Cada módulo sigue Clean Architecture internamente: `domain/ → application/ → infrastructure/ → presentation/`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API Docs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
pytest
```
