# Modulo: Autenticacion y Usuarios

Sistema JWT Bearer con control de acceso por roles (RBAC).

---

## Interfaces TypeScript

```typescript
// ── Request ──

interface LoginRequest {
  email: string;
  password: string;          // min 8 chars
}

interface RegisterRequest {
  email: string;
  full_name: string;         // min 2, max 255
  password: string;          // min 8
  phone?: string | null;
}

interface PatientLoginRequest {
  query: string;             // cedula o NHM
  query_type: "cedula" | "nhm";
}

interface UpdateProfileRequest {
  full_name?: string | null;
  phone?: string | null;
}

interface AssignRoleRequest {
  role_name: string;
}

// ── Response ──

interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  user_status: string | null;
  roles: string[];
}

interface PatientLoginResponse {
  found: boolean;
  patient: {
    id: string;
    nhm: number;
    first_name: string;
    last_name: string;
    university_relation: string;
    is_new: boolean;
  } | null;
}
```

---

## Endpoints

### 1. `POST /auth/login`

Inicio de sesion. Retorna JWT token.

**Auth:** No requerida

**Request Body:** `LoginRequest`

**Response (200):** `TokenResponse`

```json
{
  "status": "success",
  "message": "Login exitoso",
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

| Error | Condicion |
|-------|-----------|
| `401` | Credenciales incorrectas |

---

### 2. `POST /auth/register`

Registro de nuevo usuario. Asigna rol `paciente` por defecto.

**Auth:** No requerida

**Request Body:** `RegisterRequest`

**Response (201):** `UserResponse`

| Error | Condicion |
|-------|-----------|
| `409` | Email ya registrado |

---

### 3. `POST /auth/patient/login`

Login de paciente sin contrasena (por cedula o NHM).

**Auth:** No requerida

**Request Body:** `PatientLoginRequest`

**Response (200):** `PatientLoginResponse`

Si `found: false`, el paciente no existe en el sistema.

---

### 4. `GET /users/me`

Perfil del usuario autenticado.

**Auth:** `profile:read`

**Response (200):** `UserResponse`

---

### 5. `PUT /users/me`

Actualizar perfil propio.

**Auth:** `profile:update`

**Request Body:** `UpdateProfileRequest`

**Response (200):** `UserResponse`

---

### 6. `GET /users`

Listar usuarios (paginado).

**Auth:** `users:read`

**Query Params:** `page`, `page_size`

**Response (200):** `PaginatedData<UserResponse>`

---

### 7. `GET /users/{user_id}`

Obtener usuario por ID.

**Auth:** `users:read`

**Response (200):** `UserResponse`

| Error | Condicion |
|-------|-----------|
| `404` | Usuario no encontrado |

---

### 8. `POST /users/{user_id}/roles`

Asignar rol a un usuario.

**Auth:** `roles:assign`

**Request Body:** `AssignRoleRequest`

**Response (200):** Confirmacion

---

### 9. `DELETE /users/{user_id}/roles/{role_name}`

Remover rol de un usuario.

**Auth:** `roles:assign`

**Response (200):** Confirmacion
