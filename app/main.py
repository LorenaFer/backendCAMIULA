from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.shared.middleware.error_handler import (
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.shared.schemas.common import ErrorResponse, StandardResponse
from app.shared.schemas.responses import ok

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


OPENAPI_TAGS = [
    {"name": "Health", "description": "Server health check"},
    {"name": "Auth", "description": "Authentication: login, register, JWT tokens"},
    {"name": "Users", "description": "User management: CRUD, roles, permissions (RBAC)"},
    {"name": "Patients", "description": "Patient registration, search by cedula/NHM, demographics"},
    {"name": "Doctors", "description": "Doctor catalog with embedded specialty"},
    {"name": "Specialties", "description": "Medical specialty CRUD (used by doctors)"},
    {"name": "Availability", "description": "Doctor time blocks and day-off exceptions"},
    {"name": "Appointments", "description": "Scheduling: create, state machine, available slots/dates, stats"},
    {"name": "Medical Records", "description": "Clinical records (JSONB evaluation), patient history"},
    {"name": "Form Schemas", "description": "Dynamic form templates per specialty"},
    {"name": "Inventory - Medication Categories", "description": "Medication classification: antibiotics, analgesics, etc."},
    {"name": "Inventory - Medications", "description": "Medication catalog: generic name, form, controlled substance"},
    {"name": "Inventory - Suppliers", "description": "Supplier registry: RIF, contact, payment terms"},
    {"name": "Inventory - Purchase Orders", "description": "Purchase orders: create, send, receive with batch creation"},
    {"name": "Inventory - Batches", "description": "Lot tracking: FEFO, expiration dates, available quantities"},
    {"name": "Inventory - Prescriptions", "description": "Medical prescriptions with item-level dispensing status"},
    {"name": "Inventory - Dispatches", "description": "Pharmacy dispensing: FEFO algorithm, monthly limits, cancellation"},
    {"name": "Inventory - Limits", "description": "Monthly dispatch limits and authorized exceptions"},
    {"name": "Inventory - Reports", "description": "Stock reports, consumption, expiration, kardex, alerts"},
    {"name": "Dashboard", "description": "Consolidated BI: KPIs, trends, charts (cross-module aggregation)"},
    {"name": "Epidemiological Reports", "description": "MPPS reports: EPI-12 (weekly), EPI-13 (nominal), EPI-15 (monthly morbidity)"},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "REST API for the Centro Ambulatorio Medico Integral — Universidad de Los Andes (CAMIULA). "
            "Manages patients, appointments, medical records, pharmacy inventory, and epidemiological reports. "
            "Built with Clean Architecture, async SQLAlchemy, and PostgreSQL."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        redoc_url=None,
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "CAMIULA Dev Team", "url": "https://github.com/LorenaFer/backendCAMIULA"},
        license_info={"name": "MIT"},
    )

    from fastapi.openapi.docs import get_redoc_html
    from fastapi.responses import JSONResponse

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{settings.APP_NAME} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_json():
        """Download the OpenAPI spec as JSON (for Postman import)."""
        return JSONResponse(content=app.openapi())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Sobreescribir el schema 422 default de FastAPI para que ReDoc/Swagger
    # muestre nuestro envelope estándar en vez de {detail: [{loc, msg, type}]}
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        # Reemplazar el schema 422 en todos los endpoints
        error_schema = ErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        for path in schema.get("paths", {}).values():
            for method in path.values():
                responses = method.get("responses", {})
                if "422" in responses:
                    responses["422"] = {
                        "description": "Error de validación",
                        "content": {
                            "application/json": {"schema": error_schema}
                        },
                    }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi

    # Health
    @app.get("/api/health", tags=["Health"], response_model=StandardResponse[None])
    async def health_check():
        """Returns server status. Use to verify the API is running."""
        return ok(message="Servidor funcionando correctamente")

    # Module routers
    from app.modules.auth.router import router as auth_router

    app.include_router(auth_router, prefix="/api")

    from app.modules.patients.router import router as patients_router

    app.include_router(patients_router, prefix="/api")

    from app.modules.inventory.router import router as inventory_router

    app.include_router(inventory_router, prefix="/api")

    from app.modules.doctors.router import router as doctors_router

    app.include_router(doctors_router, prefix="/api")

    from app.modules.appointments.router import router as appointments_router

    app.include_router(appointments_router, prefix="/api")

    from app.modules.medical_records.router import router as medical_records_router

    app.include_router(medical_records_router, prefix="/api")

    from app.modules.dashboard.router import router as dashboard_router

    app.include_router(dashboard_router, prefix="/api")

    from app.modules.reports.router import router as reports_router

    app.include_router(reports_router, prefix="/api")

    return app


app = create_app()
