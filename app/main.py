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


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        redoc_url=None,
    )

    from fastapi.openapi.docs import get_redoc_html

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{settings.APP_NAME} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js",
        )

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

    return app


app = create_app()
