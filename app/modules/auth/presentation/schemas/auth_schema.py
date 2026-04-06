from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials for user authentication."""

    email: EmailStr = Field(description="User email address", example="doctor@camiula.edu.ve")
    password: str = Field(min_length=8, description="Account password (min 8 characters)", example="SecurePass123")

    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "doctor@camiula.edu.ve", "password": "SecurePass123"}
    })


class RegisterRequest(BaseModel):
    """New user registration payload."""

    email: EmailStr = Field(description="Unique email address", example="nuevo@ula.ve")
    full_name: str = Field(min_length=2, max_length=255, description="Full name", example="Maria Garcia")
    password: str = Field(min_length=8, description="Password (min 8 characters)", example="MiPassword123")
    phone: Optional[str] = Field(None, description="Contact phone number", example="0414-1234567")

    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "nuevo@ula.ve", "full_name": "Maria Garcia", "password": "MiPassword123", "phone": "0414-1234567"}
    })


class TokenResponse(BaseModel):
    """JWT token returned after successful authentication."""

    access_token: str = Field(description="JWT access token for Authorization header", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'", example="bearer")
    expires_in: int = Field(description="Token validity in seconds", example=1800)


class UserResponse(BaseModel):
    """User profile with assigned roles."""

    id: str = Field(description="User UUID", example="a1b2c3d4-e5f6-7890-abcd-1234567890ab")
    email: str = Field(description="User email", example="doctor@camiula.edu.ve")
    full_name: str = Field(description="Full name", example="Dr. Carlos Mendez")
    phone: Optional[str] = Field(None, description="Phone number", example="0274-2401111")
    user_status: Optional[str] = Field(None, description="Account status: ACTIVE, INACTIVE", example="ACTIVE")
    roles: List[str] = Field(description="Assigned role names", example=["doctor", "admin"])


class UpdateProfileRequest(BaseModel):
    """Fields to update on the current user's profile."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="New full name", example="Carlos A. Mendez")
    phone: Optional[str] = Field(None, description="New phone number", example="0414-9876543")


class CreateUserRequest(BaseModel):
    """Create a staff user with specific roles."""

    email: EmailStr = Field(description="Unique email", example="enfermera@camiula.edu.ve")
    full_name: str = Field(min_length=2, max_length=255, description="Full name", example="Ana Lopez")
    password: str = Field(min_length=8, description="Password", example="StaffPass123")
    phone: Optional[str] = Field(None, description="Phone", example="0274-2401111")
    roles: List[str] = Field(default=["paciente"], min_length=1, description="Roles to assign. Options: admin, doctor, analista, farmacia, paciente", example=["doctor"])
    specialty_id: Optional[str] = Field(None, description="Specialty UUID. Required when role includes 'doctor'", example="f1e2d3c4-b5a6-7890-abcd-1234567890ab")

    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "enfermera@camiula.edu.ve", "full_name": "Ana Lopez", "password": "StaffPass123", "roles": ["doctor"], "specialty_id": "f1e2d3c4-b5a6-7890-abcd-1234567890ab"}
    })


class AssignRoleRequest(BaseModel):
    """Role to assign to a user."""

    role_name: str = Field(min_length=2, max_length=50, description="Role name to assign. Options: admin, doctor, analista, farmacia, paciente", example="admin")


# ---------------------------------------------------------------------------
# Patient portal login (no password)
# ---------------------------------------------------------------------------


class PatientLoginRequest(BaseModel):
    """Authenticate patient by cedula or NHM (no password required)."""

    query: str = Field(min_length=1, max_length=30, description="Cedula number or NHM value", example="V-12345678")
    query_type: str = Field(pattern="^(cedula|nhm)$", description="Lookup type: 'cedula' or 'nhm'", example="cedula")


class PatientLoginData(BaseModel):
    """Minimal patient data returned on portal login."""

    id: str = Field(description="Patient UUID", example="b2c3d4e5-f6a7-8901-bcde-234567890abc")
    nhm: int = Field(description="Hospital Medical Number", example=1234)
    first_name: str = Field(description="First name", example="Juan")
    last_name: str = Field(description="Last name", example="Perez")
    university_relation: str = Field(description="Relation type with ULA", example="estudiante")
    is_new: bool = Field(description="True if first-time patient", example=False)


class PatientLoginResponse(BaseModel):
    """Result of patient portal authentication."""

    found: bool = Field(description="Whether the patient was found in the system", example=True)
    patient: Optional[PatientLoginData] = Field(None, description="Patient data, null if not found")
