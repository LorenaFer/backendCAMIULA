from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str


@dataclass(frozen=True)
class RegisterDTO:
    email: str
    full_name: str
    password: str
    phone: Optional[str] = None


@dataclass(frozen=True)
class TokenResponseDTO:
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    expires_in: int = 900  # 15 min en segundos (default)
