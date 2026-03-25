from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginByIdentifierRequest(BaseModel):
    """Login flexible: identifier puede ser email, cédula o username."""

    identifier: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8)
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """Response adaptado al contrato frontend: incluye user + token."""

    user: "MeResponse"
    token: str


class MeResponse(BaseModel):
    """Response para /users/me adaptado al contrato frontend."""

    id: str
    name: str
    role: str
    initials: str
    doctor_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    user_status: Optional[str]
    roles: List[str]


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None


class AssignRoleRequest(BaseModel):
    role_name: str = Field(min_length=2, max_length=50)
