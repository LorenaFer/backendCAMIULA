from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from uuid import uuid4

from app.modules.auth.domain.entities.enums import UserStatus


@dataclass
class User:
    email: str
    full_name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    external_auth: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    cedula: Optional[str] = None
    username: Optional[str] = None
    hashed_password: Optional[str] = None
    user_status: str = UserStatus.PENDING.value
    roles: list[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)
    doctor_id: Optional[str] = None

    def get_external_sub(self, provider: str) -> Optional[str]:
        """Obtiene el sub de un proveedor externo específico."""
        if self.external_auth and provider in self.external_auth:
            return self.external_auth[provider].get("sub")
        return None
