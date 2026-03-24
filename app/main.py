from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.shared.middleware.error_handler import app_exception_handler
from app.shared.schemas.common import MessageResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppException, app_exception_handler)

    # Health
    @app.get("/api/health", response_model=MessageResponse, tags=["Health"])
    async def health_check():
        return MessageResponse(message="OK")

    # TODO: Register module routers here as they are developed
    # from app.modules.auth.router import router as auth_router
    # app.include_router(auth_router, prefix="/api")

    return app


app = create_app()
