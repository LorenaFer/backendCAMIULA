from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8)
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


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


# ---------------------------------------------------------------------------
# Patient portal login (no password)
# ---------------------------------------------------------------------------


class PatientLoginRequest(BaseModel):
    query: str = Field(min_length=1, max_length=30)
    query_type: str = Field(pattern="^(cedula|nhm)$")


class PatientLoginData(BaseModel):
    id: str
    nhm: int
    first_name: str
    last_name: str
    university_relation: str
    is_new: bool


class PatientLoginResponse(BaseModel):
    found: bool
    patient: Optional[PatientLoginData] = None
