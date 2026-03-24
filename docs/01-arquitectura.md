# Arquitectura del Proyecto

## Monolito Modular + Clean Architecture

Este backend usa una arquitectura de **Monolito Modular**: una sola aplicación FastAPI donde cada dominio de negocio vive en su propio módulo independiente. Dentro de cada módulo, se aplica **Clean Architecture**.

### ¿Por qué Monolito Modular?

- **Trabajo en paralelo**: cada dev trabaja en su módulo sin pisar el código de los demás
- **Bajo acoplamiento**: los módulos no se importan entre sí
- **Simple de desplegar**: es una sola app, no necesitamos orquestar microservicios
- **Fácil de escalar después**: si un módulo crece mucho, se puede extraer a un servicio aparte

## Estructura General

```
backendCAMIULA/
├── app/
│   ├── core/              ← Configuración global (NO tocar sin coordinar)
│   ├── shared/            ← Código compartido entre módulos
│   │   ├── database/      ← Engine, session de SQLAlchemy
│   │   ├── middleware/     ← Auth, manejo de errores
│   │   └── schemas/       ← Schemas comunes (paginación, mensajes)
│   ├── modules/           ← AQUÍ VIVE CADA MÓDULO
│   │   ├── auth/
│   │   ├── patients/
│   │   ├── appointments/
│   │   └── inventory/
│   └── main.py            ← Entry point, registra los routers
├── alembic/               ← Migraciones de BD
├── tests/
├── docs/                  ← Documentación del equipo
└── requirements.txt
```

## Capas de Clean Architecture (dentro de cada módulo)

```
modules/auth/                      ← Ejemplo con el módulo auth
│
├── domain/                        ← CAPA DE DOMINIO (lo más interno)
│   ├── entities/                  ← Entidades puras (dataclasses)
│   │   └── user.py                   User(id, email, full_name, ...)
│   ├── repositories/              ← Interfaces (contratos abstractos)
│   │   └── user_repository.py        class UserRepository(ABC)
│   └── services/                  ← Lógica de negocio pura
│       └── auth_service.py           register(), authenticate()
│
├── application/                   ← CAPA DE APLICACIÓN (orquestación)
│   ├── use_cases/                 ← Casos de uso concretos
│   │   ├── register_user.py          RegisterUserUseCase
│   │   └── login_user.py             LoginUserUseCase
│   └── dtos/                      ← Data Transfer Objects
│       └── user_dto.py               CreateUserDTO, LoginDTO
│
├── infrastructure/                ← CAPA DE INFRAESTRUCTURA (detalles técnicos)
│   ├── models.py                  ← Modelo SQLAlchemy (tabla de BD)
│   └── repositories/
│       └── sqlalchemy_user_repo.py   Implementación concreta del repositorio
│
├── presentation/                  ← CAPA DE PRESENTACIÓN (HTTP)
│   ├── routes/                    ← Endpoints FastAPI
│   │   └── auth_routes.py            POST /register, POST /login
│   └── schemas/                   ← Schemas Pydantic (request/response)
│       └── user_schema.py            UserCreateRequest, UserResponse
│
└── router.py                      ← Router principal del módulo
```

## Regla de Dependencia

Las dependencias van **hacia adentro**:

```
Presentation → Application → Domain ← Infrastructure
```

- `domain/` NO importa nada de las otras capas
- `application/` solo importa de `domain/`
- `infrastructure/` implementa las interfaces de `domain/`
- `presentation/` usa `application/` y `infrastructure/`

Esto significa que puedes cambiar la base de datos (infraestructura) sin tocar la lógica de negocio (dominio).
