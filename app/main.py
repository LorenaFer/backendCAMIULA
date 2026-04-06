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

    def _resolve_ref(ref_str: str, spec: dict) -> dict:
        """Resolve a $ref string like '#/components/schemas/X' to the actual schema."""
        if not ref_str or not ref_str.startswith("#/"):
            return {}
        parts = ref_str.lstrip("#/").split("/")
        node = spec
        for p in parts:
            node = node.get(p, {})
        return node

    def _add_code_samples(path: str, method: str, details: dict, schema: dict = None):
        """Inject x-codeSamples for ReDoc display."""
        import json as _json
        has_body = method in ("post", "put", "patch")

        # Build path with example values for path params
        example_path = path
        for param in details.get("parameters", []):
            if param.get("in") == "path":
                name = param["name"]
                ex = param.get("schema", {}).get("example", f"<{name}>")
                example_path = example_path.replace("{" + name + "}", str(ex))

        url = "http://localhost:8000" + example_path

        # Collect query params — include ALL with examples, not just required
        _PARAM_EXAMPLES = {
            "page": "1", "page_size": "20", "search": "amoxicilina",
            "fecha": "2026-04-15", "doctor_id": "<doctor_uuid>",
            "medication_id": "<medication_uuid>", "patient_id": "<patient_uuid>",
            "status": "active", "period": "2026-03", "year": "2026",
            "month": "4", "week": "15", "threshold_days": "90",
            "date_from": "2026-01-01", "date_to": "2026-12-31",
            "alert_status": "active", "alert_level": "critical",
            "movement_type": "entry", "prescription_id": "<prescription_uuid>",
            "q": "perez", "mes": "2026-04", "nhm": "1234",
            "cedula": "V-12345678", "es_nuevo": "false",
        }
        query_parts = []
        for param in details.get("parameters", []):
            if param.get("in") != "query":
                continue
            name = param["name"]
            ex = param.get("schema", {}).get("example")
            if not ex:
                ex = _PARAM_EXAMPLES.get(name)
            if param.get("required"):
                query_parts.append(f"{name}={ex or 'value'}")
            elif ex:
                query_parts.append(f"{name}={ex}")
        # For GET with many optional params, show the 2-3 most useful
        if not any(p.get("required") for p in details.get("parameters", []) if p.get("in") == "query"):
            query_parts = query_parts[:3]
        qs = "?" + "&".join(query_parts) if query_parts else ""

        # Get request body example — resolve $ref if needed
        body_example = ""
        body_json_str = ""
        rb_schema = details.get("requestBody", {}).get("content", {}).get(
            "application/json", {}
        ).get("schema", {})

        example_data = None
        if rb_schema:
            # Direct example on the schema
            if rb_schema.get("example"):
                example_data = rb_schema["example"]
            # Resolve $ref to component schema
            elif rb_schema.get("$ref"):
                resolved = _resolve_ref(rb_schema["$ref"], schema)
                if resolved.get("example"):
                    example_data = resolved["example"]
                elif resolved.get("properties"):
                    # Build example from individual field examples
                    example_data = {}
                    for fname, fprop in resolved.get("properties", {}).items():
                        if "example" in fprop:
                            example_data[fname] = fprop["example"]
                        elif fprop.get("default") is not None:
                            example_data[fname] = fprop["default"]

        if example_data:
            body_example = _json.dumps(example_data, indent=2)
            body_json_str = _json.dumps(example_data)

        # --- cURL ---
        curl_lines = [f'curl -X {method.upper()} "{url}{qs}"']
        curl_lines.append('  -H "Authorization: Bearer $TOKEN"')
        if has_body:
            curl_lines.append('  -H "Content-Type: application/json"')
            if body_example:
                curl_lines.append(f"  -d '{body_json_str}'")
        curl = " \\\n".join(curl_lines)

        # --- Python ---
        py_lines = ["import httpx", ""]
        py_lines.append('BASE = "http://localhost:8000"')
        py_lines.append('HEADERS = {"Authorization": "Bearer <token>"}')
        py_lines.append("")
        if has_body and body_example:
            py_lines.append(f"data = {body_example}")
            py_lines.append("")
            py_lines.append(
                f'resp = httpx.{method}(f"{{BASE}}{example_path}{qs}", '
                f'json=data, headers=HEADERS)'
            )
        else:
            py_lines.append(
                f'resp = httpx.{method}(f"{{BASE}}{example_path}{qs}", '
                f'headers=HEADERS)'
            )
        py_lines.append("print(resp.json())")
        python = "\n".join(py_lines)

        # --- JavaScript ---
        js_lines = []
        if has_body and body_example:
            js_lines.append(
                f'const resp = await fetch("{url}{qs}", {{'
            )
            js_lines.append(f'  method: "{method.upper()}",')
            js_lines.append('  headers: {')
            js_lines.append('    "Authorization": "Bearer <token>",')
            js_lines.append('    "Content-Type": "application/json",')
            js_lines.append("  },")
            js_lines.append(f"  body: JSON.stringify({body_json_str}),")
            js_lines.append("});")
        else:
            js_lines.append(
                f'const resp = await fetch("{url}{qs}", {{'
            )
            js_lines.append(f'  method: "{method.upper()}",')
            js_lines.append('  headers: { "Authorization": "Bearer <token>" },')
            js_lines.append("});")
        js_lines.append("const data = await resp.json();")
        js_lines.append("console.log(data);")
        javascript = "\n".join(js_lines)

        details["x-codeSamples"] = [
            {"lang": "cURL", "label": "cURL", "source": curl},
            {"lang": "Python", "label": "Python", "source": python},
            {"lang": "JavaScript", "label": "JavaScript", "source": javascript},
        ]

    # Sobreescribir los schemas de OpenAPI para que ReDoc/Swagger
    # muestre nuestro envelope estandar { status, message, data } en todas
    # las respuestas, y el formato de error estandar en 422.
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )

        # Schema del envelope estandar de error
        error_schema = ErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )

        # Schema del envelope estandar de exito
        # { "status": "success", "message": "...", "data": <original_schema> }
        def wrap_with_envelope(original_schema, description="Successful Response"):
            return {
                "description": description,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["status", "message"],
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "example": "success",
                                    "description": "Always 'success' for 2xx responses",
                                },
                                "message": {
                                    "type": "string",
                                    "example": "Operation completed successfully",
                                    "description": "Human-readable result message",
                                },
                                "data": original_schema or {"nullable": True},
                            },
                        }
                    }
                },
            }

        for path_str, path_methods in schema.get("paths", {}).items():
            for method, details in path_methods.items():
                if not isinstance(details, dict):
                    continue
                responses = details.get("responses", {})

                # Wrap 200 responses with envelope
                for code in ("200", "201"):
                    if code in responses:
                        resp = responses[code]
                        content = resp.get("content", {})
                        json_content = content.get("application/json", {})
                        original_schema = json_content.get("schema")

                        # Skip if already has our envelope:
                        # 1. Inline schema with status+message properties
                        # 2. $ref to StandardResponse_* (from response_model=)
                        if original_schema and isinstance(original_schema, dict):
                            # Check inline properties
                            if ("properties" in original_schema and
                                    "status" in original_schema.get("properties", {})):
                                continue
                            # Check $ref to StandardResponse
                            ref = original_schema.get("$ref", "")
                            if "StandardResponse" in ref:
                                continue

                        desc = resp.get("description", "Successful Response")
                        responses[code] = wrap_with_envelope(original_schema, desc)

                # Replace 422 with our error envelope
                if "422" in responses:
                    responses["422"] = {
                        "description": "Validation error — one or more fields failed validation",
                        "content": {
                            "application/json": {
                                "schema": error_schema,
                                "example": {
                                    "status": "error",
                                    "message": "Error de validacion",
                                    "data": [{"field": "email", "message": "Invalid email format"}],
                                },
                            }
                        },
                    }

                # Add standard error responses (401, 404)
                _error_example = lambda msg: {
                    "content": {
                        "application/json": {
                            "schema": error_schema,
                            "example": {"status": "error", "message": msg, "data": None},
                        }
                    }
                }

                # Determine which error codes to add based on method and path
                has_auth = any(
                    p.get("name") == "authorization"
                    for p in details.get("parameters", [])
                    if p.get("in") == "header"
                ) or details.get("security")

                if "401" not in responses:
                    responses["401"] = {
                        "description": "Unauthorized — missing or invalid JWT token",
                        **_error_example("Token invalido o expirado"),
                    }

                if method in ("get",) and "{" in path_str and "404" not in responses:
                    responses["404"] = {
                        "description": "Not found — the requested resource does not exist",
                        **_error_example("Recurso no encontrado"),
                    }

                if method in ("post",) and "409" not in responses:
                    responses["409"] = {
                        "description": "Conflict — a resource with this identifier already exists",
                        **_error_example("Ya existe un recurso con ese identificador"),
                    }

                # Add code samples (x-codeSamples) for ReDoc
                _add_code_samples(path_str, method, details, schema=schema)

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
