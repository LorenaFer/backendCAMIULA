from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateUserDTO:
    email: str
    full_name: str
    phone: Optional[str] = None
    auth0_sub: Optional[str] = None
    hashed_password: Optional[str] = None


@dataclass(frozen=True)
class UpdateUserDTO:
    full_name: Optional[str] = None
    phone: Optional[str] = None


@dataclass(frozen=True)
class AssignRoleDTO:
    user_id: str
    role_name: str
