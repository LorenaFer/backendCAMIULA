from fastapi import APIRouter

from app.modules.auth.presentation.routes.auth_routes import router as auth_router
from app.modules.auth.presentation.routes.user_routes import router as user_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(user_router)
