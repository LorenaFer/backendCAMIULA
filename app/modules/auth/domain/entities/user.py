from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
from uuid import uuid4


@dataclass
class User:
    email: str
    full_name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    external_auth: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    hashed_password: Optional[str] = None
    user_status: str = "PENDING"
    roles: list[str] = field(default_factory=list)
    permissions: Set[str] = field(default_factory=set)

    def get_external_sub(self, provider: str) -> Optional[str]:
        """Gets the sub from a specific external providífico."""
        if self.external_auth and provider in self.external_auth:
            return self.external_auth[provider].get("sub")
        return None
