"""
Instancia singleton del caché de permisos.

Importable por todos los módulos:
    from app.shared.middleware.permission_cache import permission_cache
"""

from app.core.config import get_settings
from app.modules.auth.infrastructure.cache.permission_cache import PermissionCache

settings = get_settings()

permission_cache = PermissionCache(ttl_seconds=settings.PERMISSION_CACHE_TTL_SECONDS)
