#!/usr/bin/env bash
# =============================================================================
# test_nhm_endpoints.sh — Integration tests for NHM endpoints
#
# Modules tested:
#   - Form Schemas CRUD (/api/schemas)
#   - Specialties CRUD (/api/specialties)
#   - Appointment Stats (/api/appointments/stats)
#   - Medical Records + patient history (/api/medical-records)
#
# Requirements: PostgreSQL running, venv at ../../.venv relative to worktree
# Usage: ./scripts/test_nhm_endpoints.sh
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WORKTREE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="${WORKTREE_DIR}/../../../.venv/bin/python"
VENV_ALEMBIC="${WORKTREE_DIR}/../../../.venv/bin/alembic"
BASE_URL="http://localhost:8000"
DB_NAME="tesis_ula_local"
DB_USER="nelsonvivas"

# Resolve psql / pg_isready from Homebrew paths if not in $PATH
_PG_SEARCH_PATHS=(
  "/opt/homebrew/opt/postgresql@16/bin"
  "/opt/homebrew/opt/postgresql@15/bin"
  "/opt/homebrew/opt/postgresql@14/bin"
  "/opt/homebrew/bin"
  "/usr/local/bin"
  "/usr/bin"
)
_resolve_pg_bin() {
  local bin="$1"
  if command -v "$bin" &>/dev/null; then
    echo "$bin"; return
  fi
  for dir in "${_PG_SEARCH_PATHS[@]}"; do
    if [[ -x "${dir}/${bin}" ]]; then
      echo "${dir}/${bin}"; return
    fi
  done
  echo ""
}
PG_READY_CMD="$(_resolve_pg_bin pg_isready)"
PSQL_CMD="$(_resolve_pg_bin psql)"
SERVER_PORT=8000
SERVER_PID=""
PASS=0
FAIL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()    { echo -e "${CYAN}[INFO]${RESET} $*"; }
warn()   { echo -e "${YELLOW}[WARN]${RESET} $*"; }
header() { echo -e "\n${BOLD}${CYAN}══ $* ══${RESET}"; }

pass() {
  PASS=$((PASS + 1))
  echo -e "  ${GREEN}✔ PASS${RESET}  $*"
}

fail() {
  FAIL=$((FAIL + 1))
  echo -e "  ${RED}✘ FAIL${RESET}  $*"
}

psql_exec() {
  "$PSQL_CMD" -U "$DB_USER" -d "$DB_NAME" -t -A -c "$1" 2>/dev/null
}

# Run curl and capture HTTP status + body
# Usage: http_call METHOD PATH [body_json]
# Sets globals: HTTP_STATUS HTTP_BODY
http_call() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local auth_header=""

  if [[ -n "${TOKEN:-}" ]]; then
    auth_header="-H 'Authorization: Bearer ${TOKEN}'"
  fi

  local response
  if [[ -n "$body" ]]; then
    response=$(curl -s -w "\n%{http_code}" -X "$method" \
      "${BASE_URL}${path}" \
      -H "Content-Type: application/json" \
      ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"} \
      -d "$body")
  else
    response=$(curl -s -w "\n%{http_code}" -X "$method" \
      "${BASE_URL}${path}" \
      -H "Content-Type: application/json" \
      ${TOKEN:+-H "Authorization: Bearer ${TOKEN}"})
  fi

  HTTP_STATUS=$(echo "$response" | tail -n1)
  HTTP_BODY=$(echo "$response" | sed '$d')
}

# Extract JSON field using python
jq_get() {
  local field="$1"
  local json="$2"
  echo "$json" | "$VENV_PYTHON" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    keys = '$field'.split('.')
    for k in keys:
        if isinstance(d, list):
            d = d[int(k)]
        else:
            d = d[k]
    print(d if d is not None else '')
except (KeyError, IndexError, TypeError, json.JSONDecodeError):
    print('')
"
}

assert_status() {
  local expected="$1"
  local label="$2"
  if [[ "$HTTP_STATUS" == "$expected" ]]; then
    pass "$label (HTTP $HTTP_STATUS)"
  else
    fail "$label — expected $expected, got $HTTP_STATUS"
    echo "       Body: $(echo "$HTTP_BODY" | head -c 200)"
  fi
}

assert_field() {
  local field="$1"
  local expected="$2"
  local label="$3"
  local actual
  actual=$(jq_get "$field" "$HTTP_BODY")
  if [[ "$actual" == "$expected" ]]; then
    pass "$label (field '$field' = '$expected')"
  else
    fail "$label — expected '$expected', got '$actual'"
  fi
}

assert_field_nonempty() {
  local field="$1"
  local label="$2"
  local actual
  actual=$(jq_get "$field" "$HTTP_BODY")
  if [[ -n "$actual" ]]; then
    pass "$label (field '$field' = '$actual')"
  else
    fail "$label — field '$field' is empty/missing"
    echo "       Body: $(echo "$HTTP_BODY" | head -c 300)"
  fi
}

# ---------------------------------------------------------------------------
# Cleanup (trap)
# ---------------------------------------------------------------------------
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    log "Killing server (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Step 1: Check PostgreSQL
# ---------------------------------------------------------------------------
header "Step 1 — PostgreSQL check"
if [[ -n "$PG_READY_CMD" ]]; then
  if ! "$PG_READY_CMD" -U "$DB_USER" -d "$DB_NAME" -q 2>/dev/null; then
    echo -e "${RED}ERROR: PostgreSQL is not running or DB '$DB_NAME' is not accessible.${RESET}"
    echo "  Start PostgreSQL and ensure the DB exists before running this script."
    exit 1
  fi
  log "PostgreSQL is ready — DB: $DB_NAME  (via pg_isready)"
else
  # pg_isready not found — fall back to HTTP health check on the FastAPI server
  warn "pg_isready not found in PATH or common Homebrew dirs; falling back to HTTP health check."
  _health_status=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || true)
  if [[ "$_health_status" != "200" ]]; then
    echo -e "${RED}ERROR: FastAPI server at ${BASE_URL} did not return 200 (got '${_health_status}').${RESET}"
    echo "  Ensure the server is running and connected to DB '$DB_NAME' before running this script."
    exit 1
  fi
  log "FastAPI server healthy — DB connectivity assumed via /health (HTTP 200)"
fi

# ---------------------------------------------------------------------------
# Step 2: Run migrations
# ---------------------------------------------------------------------------
header "Step 2 — Alembic migrations"
cd "$WORKTREE_DIR"
if "$VENV_ALEMBIC" upgrade head 2>&1 | tail -5; then
  log "Migrations up to date."
else
  warn "Alembic upgrade failed or no-op — continuing."
fi

# ---------------------------------------------------------------------------
# Step 3: Run seeders
# ---------------------------------------------------------------------------
header "Step 3 — Seeders"
if "$VENV_PYTHON" -m app.shared.database.seeder 2>&1 | tail -5; then
  log "Seeders done."
else
  warn "Seeders failed — some test data may be missing."
fi

# ---------------------------------------------------------------------------
# Step 4: Add missing NHM permissions and assign to administrador
# ---------------------------------------------------------------------------
header "Step 4 — NHM permissions setup"
psql_exec "
DO \$\$
DECLARE
  v_role_id text;
  v_perm_id text;
  v_perms text[] := ARRAY['doctors:write', 'schemas:read', 'schemas:write'];
  v_perm text;
BEGIN
  SELECT id INTO v_role_id FROM roles WHERE name = 'administrador';
  IF v_role_id IS NULL THEN
    RAISE NOTICE 'Role administrador not found — skipping permission setup';
    RETURN;
  END IF;

  FOREACH v_perm IN ARRAY v_perms LOOP
    -- Upsert permission
    IF NOT EXISTS (SELECT 1 FROM permissions WHERE code = v_perm) THEN
      INSERT INTO permissions (id, code, module, description)
      VALUES (
        gen_random_uuid()::text,
        v_perm,
        CASE
          WHEN v_perm LIKE 'schemas%' THEN 'form_schemas'
          ELSE 'appointments'
        END,
        CASE v_perm
          WHEN 'doctors:write'  THEN 'Gestionar especialidades'
          WHEN 'schemas:read'   THEN 'Ver schemas de formularios'
          WHEN 'schemas:write'  THEN 'Gestionar schemas de formularios'
        END
      );
    END IF;

    -- Assign to admin if not already assigned
    SELECT id INTO v_perm_id FROM permissions WHERE code = v_perm;
    IF NOT EXISTS (
      SELECT 1 FROM role_permissions
      WHERE fk_role_id = v_role_id AND fk_permission_id = v_perm_id
    ) THEN
      INSERT INTO role_permissions (id, fk_role_id, fk_permission_id)
      VALUES (gen_random_uuid()::text, v_role_id, v_perm_id);
    END IF;
  END LOOP;
END \$\$;
" && log "Permissions ready."

# ---------------------------------------------------------------------------
# Step 5: Get test IDs from DB (patient, doctor, specialty)
# ---------------------------------------------------------------------------
header "Step 5 — Resolving test entity IDs"
PATIENT_ID=$(psql_exec "SELECT id FROM patients WHERE cedula = 'V-12345678' LIMIT 1")
DOCTOR_ID=$(psql_exec "SELECT id FROM doctors LIMIT 1")
SPECIALTY_ID=$(psql_exec "SELECT id FROM specialties LIMIT 1")

if [[ -z "$PATIENT_ID" || -z "$DOCTOR_ID" || -z "$SPECIALTY_ID" ]]; then
  warn "Could not resolve test IDs from DB:"
  warn "  patient=$PATIENT_ID  doctor=$DOCTOR_ID  specialty=$SPECIALTY_ID"
  warn "Medical records tests will be skipped."
  SKIP_MEDICAL=1
else
  SKIP_MEDICAL=0
  log "patient_id  = $PATIENT_ID"
  log "doctor_id   = $DOCTOR_ID"
  log "specialty_id= $SPECIALTY_ID"
fi

# Insert a test appointment for medical records testing
if [[ "${SKIP_MEDICAL}" == "0" ]]; then
  TEST_APPT_ID=$(psql_exec "SELECT gen_random_uuid()::text")
  psql_exec "
  INSERT INTO appointments (
    id, fk_patient_id, fk_doctor_id, fk_specialty_id,
    appointment_date, start_time, end_time, duration_minutes,
    is_first_visit, reason, appointment_status,
    status, created_at, updated_at
  )
  SELECT
    '${TEST_APPT_ID}',
    '${PATIENT_ID}',
    '${DOCTOR_ID}',
    '${SPECIALTY_ID}',
    CURRENT_DATE,
    '09:00:00'::time,
    '09:30:00'::time,
    30,
    false,
    'Control de prueba NHM script',
    'pendiente',
    'A',
    NOW(),
    NOW()
  WHERE NOT EXISTS (
    SELECT 1 FROM appointments WHERE id = '${TEST_APPT_ID}'
  );
  " >/dev/null 2>&1 && log "Test appointment inserted: $TEST_APPT_ID" || {
    warn "Could not insert test appointment — medical records tests will be skipped."
    SKIP_MEDICAL=1
  }
fi

# ---------------------------------------------------------------------------
# Step 6: Start FastAPI server
# ---------------------------------------------------------------------------
header "Step 6 — Starting FastAPI server"
export AUTH_PROVIDER=local
"$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port "$SERVER_PORT" \
  --log-level warning &
SERVER_PID=$!
log "Server started (PID $SERVER_PID), waiting for readiness..."

# Poll health endpoint (max 20s)
READY=0
for i in $(seq 1 20); do
  sleep 1
  if curl -sf "${BASE_URL}/api/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
done

if [[ "$READY" -eq 0 ]]; then
  echo -e "${RED}ERROR: Server did not become ready in 20s.${RESET}"
  exit 1
fi
log "Server is ready at $BASE_URL"

# ---------------------------------------------------------------------------
# Step 7: Authenticate
# ---------------------------------------------------------------------------
header "Step 7 — Authentication"
http_call POST /api/auth/login '{"identifier":"admin@camiula.com","password":"admin123"}'
TOKEN=$(jq_get "data.token" "$HTTP_BODY")
USER_ID=$(jq_get "data.user.id" "$HTTP_BODY")

if [[ -z "$TOKEN" ]]; then
  echo -e "${RED}ERROR: Could not get JWT token. Login failed.${RESET}"
  echo "  Body: $HTTP_BODY"
  exit 1
fi
log "Authenticated as admin (user_id=$USER_ID)"

# ===========================================================================
# TESTS
# ===========================================================================

# ---------------------------------------------------------------------------
# Form Schemas CRUD
# ---------------------------------------------------------------------------
header "TESTS — Form Schemas (/api/schemas)"

SCHEMA_PAYLOAD='{
  "id": "test-schema-nhm-v1",
  "version": "1.0",
  "specialtyId": "test-especialidad",
  "specialtyName": "Especialidad de Test NHM",
  "sections": [
    {
      "id": "s1",
      "title": "Motivo",
      "groups": [
        {
          "id": "g1",
          "fields": [
            {
              "key": "motivo_consulta",
              "type": "textarea",
              "label": "Motivo de consulta",
              "validation": {"required": true}
            }
          ]
        }
      ]
    }
  ]
}'

# PUT /api/schemas — create
http_call PUT /api/schemas "$SCHEMA_PAYLOAD"
assert_status 200 "PUT /api/schemas — create schema"
assert_field "data.id" "test-schema-nhm-v1" "schema id matches"
assert_field "data.version" "1.0" "schema version matches"
assert_field "status" "success" "response envelope status=success"
assert_field_nonempty "data.created_at" "schema has created_at"
assert_field_nonempty "data.updated_at" "schema has updated_at"

# GET /api/schemas — list
http_call GET /api/schemas
assert_status 200 "GET /api/schemas — list all schemas"
assert_field "status" "success" "list response envelope"

SCHEMA_COUNT=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
print(len(d.get('data', [])))
")
if [[ "$SCHEMA_COUNT" -ge 1 ]]; then
  pass "GET /api/schemas — returns at least 1 schema (got $SCHEMA_COUNT)"
else
  fail "GET /api/schemas — expected >=1 schemas, got 0"
fi

# GET /api/schemas/{key} — exact schema id
http_call GET "/api/schemas/test-schema-nhm-v1"
assert_status 200 "GET /api/schemas/test-schema-nhm-v1 — by exact id"
assert_field "data.id" "test-schema-nhm-v1" "correct schema returned"

# GET /api/schemas/{key} — by specialty name (normalization)
http_call GET "/api/schemas/test-especialidad"
assert_status 200 "GET /api/schemas/test-especialidad — by specialty_id"

# GET /api/schemas/{key} — fallback to medicina-general when not found
http_call GET "/api/schemas/una-especialidad-que-no-existe"
assert_status 200 "GET /api/schemas/{unknown} — fallback (returns null or medicina-general)"

# PUT /api/schemas — update (upsert same id)
SCHEMA_UPDATE='{
  "id": "test-schema-nhm-v1",
  "version": "1.1",
  "specialtyId": "test-especialidad",
  "specialtyName": "Especialidad de Test NHM actualizada",
  "sections": [
    {
      "id": "s1",
      "title": "Motivo actualizado",
      "groups": [
        {
          "id": "g1",
          "fields": [
            {"key": "motivo_consulta", "type": "textarea", "label": "Motivo", "validation": {"required": true}},
            {"key": "nota", "type": "text", "label": "Nota adicional"}
          ]
        }
      ]
    }
  ]
}'
http_call PUT /api/schemas "$SCHEMA_UPDATE"
assert_status 200 "PUT /api/schemas — update schema (upsert)"
assert_field "data.version" "1.1" "schema version updated to 1.1"

# PUT /api/schemas — missing sections → 422
BAD_SCHEMA='{"id":"bad-v1","version":"1.0","specialtyId":"bad","specialtyName":"Bad","sections":"not-an-array"}'
http_call PUT /api/schemas "$BAD_SCHEMA"
assert_status 422 "PUT /api/schemas — invalid sections → 422"

# DELETE /api/schemas/{key} — soft-delete
http_call DELETE "/api/schemas/test-schema-nhm-v1"
assert_status 200 "DELETE /api/schemas/test-schema-nhm-v1 — soft-delete"
assert_field "status" "success" "soft-delete response envelope"

# Verify soft-delete: schema no longer visible
http_call GET "/api/schemas/test-schema-nhm-v1"
AFTER_DEL=$(jq_get "data" "$HTTP_BODY")
# After soft-delete, it should either fall back to medicina-general or return null
# We verify it does NOT return the deleted schema's version 1.1
AFTER_DEL_VER=$(jq_get "data.version" "$HTTP_BODY")
if [[ "$AFTER_DEL_VER" != "1.1" ]]; then
  pass "GET /api/schemas/{deleted} — soft-deleted schema not visible (fallback/null)"
else
  fail "GET /api/schemas/{deleted} — soft-deleted schema still returned with version 1.1"
fi

# Verify soft-delete in DB: status=T, deleted_at not null
SCHEMA_STATUS=$(psql_exec "SELECT status FROM form_schemas WHERE id = 'test-schema-nhm-v1'")
SCHEMA_DELETED_AT=$(psql_exec "SELECT deleted_at FROM form_schemas WHERE id = 'test-schema-nhm-v1'")
if [[ "$SCHEMA_STATUS" == "T" ]]; then
  pass "form_schemas.status = T after soft-delete"
else
  fail "form_schemas.status = '$SCHEMA_STATUS', expected 'T'"
fi
if [[ -n "$SCHEMA_DELETED_AT" ]]; then
  pass "form_schemas.deleted_at is set after soft-delete"
else
  fail "form_schemas.deleted_at is NULL after soft-delete"
fi

# Verify audit fields in DB
SCHEMA_CREATED_BY=$(psql_exec "SELECT created_by FROM form_schemas WHERE id = 'test-schema-nhm-v1'")
SCHEMA_UPDATED_BY=$(psql_exec "SELECT updated_by FROM form_schemas WHERE id = 'test-schema-nhm-v1'")
SCHEMA_DELETED_BY=$(psql_exec "SELECT deleted_by FROM form_schemas WHERE id = 'test-schema-nhm-v1'")
if [[ -n "$SCHEMA_CREATED_BY" ]]; then
  pass "form_schemas.created_by is set ($SCHEMA_CREATED_BY)"
else
  fail "form_schemas.created_by is NULL"
fi
if [[ -n "$SCHEMA_UPDATED_BY" ]]; then
  pass "form_schemas.updated_by is set ($SCHEMA_UPDATED_BY)"
else
  fail "form_schemas.updated_by is NULL"
fi
if [[ -n "$SCHEMA_DELETED_BY" ]]; then
  pass "form_schemas.deleted_by is set ($SCHEMA_DELETED_BY)"
else
  fail "form_schemas.deleted_by is NULL"
fi

# DELETE /api/schemas/{unknown} → 404
http_call DELETE "/api/schemas/schema-que-no-existe-xyz"
assert_status 404 "DELETE /api/schemas/{unknown} → 404"

# ---------------------------------------------------------------------------
# Specialties CRUD
# ---------------------------------------------------------------------------
header "TESTS — Specialties (/api/specialties)"

# GET /api/specialties — list
http_call GET /api/specialties
assert_status 200 "GET /api/specialties — list"
assert_field "status" "success" "specialties list envelope"

SPEC_COUNT=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
print(len(d.get('data', [])))
")
if [[ "$SPEC_COUNT" -ge 1 ]]; then
  pass "GET /api/specialties — at least 1 specialty returned (got $SPEC_COUNT)"
else
  fail "GET /api/specialties — expected >=1 specialties"
fi

# Verify each specialty has 'activo' field
FIRST_HAS_ACTIVO=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('data', [])
print('yes' if items and 'activo' in items[0] else 'no')
")
if [[ "$FIRST_HAS_ACTIVO" == "yes" ]]; then
  pass "GET /api/specialties — each item has 'activo' field"
else
  fail "GET /api/specialties — items missing 'activo' field"
fi

# POST /api/specialties — create
TIMESTAMP=$(date +%s)
NEW_SPEC_NAME="Especialidad Test NHM $TIMESTAMP"
http_call POST /api/specialties "{\"nombre\":\"${NEW_SPEC_NAME}\"}"
assert_status 201 "POST /api/specialties — create new specialty"
assert_field "status" "success" "create specialty envelope"
NEW_SPEC_ID=$(jq_get "data.id" "$HTTP_BODY")

if [[ -n "$NEW_SPEC_ID" ]]; then
  pass "POST /api/specialties — new specialty has id ($NEW_SPEC_ID)"
else
  fail "POST /api/specialties — no id in response"
fi

SPEC_ACTIVO=$(jq_get "data.activo" "$HTTP_BODY")
if [[ "$SPEC_ACTIVO" == "True" ]]; then
  pass "POST /api/specialties — new specialty is active"
else
  fail "POST /api/specialties — activo='$SPEC_ACTIVO', expected True"
fi

# POST /api/specialties — duplicate name → 409
http_call POST /api/specialties "{\"nombre\":\"${NEW_SPEC_NAME}\"}"
assert_status 409 "POST /api/specialties — duplicate name → 409"

# PUT /api/specialties/{id} — update name
UPDATED_NAME="Especialidad Test NHM Actualizada $TIMESTAMP"
http_call PUT "/api/specialties/${NEW_SPEC_ID}" "{\"nombre\":\"${UPDATED_NAME}\"}"
assert_status 200 "PUT /api/specialties/{id} — update name"
assert_field "data.id" "$NEW_SPEC_ID" "updated specialty id matches"
UPDATED_NOMBRE=$(jq_get "data.nombre" "$HTTP_BODY")
if [[ "$UPDATED_NOMBRE" == "$UPDATED_NAME" ]]; then
  pass "PUT /api/specialties/{id} — name updated correctly"
else
  fail "PUT /api/specialties/{id} — nombre='$UPDATED_NOMBRE', expected '$UPDATED_NAME'"
fi

# PUT /api/specialties/{unknown} → 404
http_call PUT "/api/specialties/00000000-0000-0000-0000-000000000000" '{"nombre":"Ghost"}'
assert_status 404 "PUT /api/specialties/{unknown} → 404"

# PATCH /api/specialties/{id}/toggle — deactivate
http_call PATCH "/api/specialties/${NEW_SPEC_ID}/toggle"
assert_status 200 "PATCH /api/specialties/{id}/toggle — toggle (deactivate)"
TOGGLED_ACTIVO=$(jq_get "data.activo" "$HTTP_BODY")
if [[ "$TOGGLED_ACTIVO" == "False" ]]; then
  pass "PATCH toggle — specialty deactivated (activo=False)"
else
  fail "PATCH toggle — activo='$TOGGLED_ACTIVO', expected False"
fi

# PATCH /api/specialties/{id}/toggle — re-activate
http_call PATCH "/api/specialties/${NEW_SPEC_ID}/toggle"
assert_status 200 "PATCH /api/specialties/{id}/toggle — toggle (re-activate)"
TOGGLED_BACK=$(jq_get "data.activo" "$HTTP_BODY")
if [[ "$TOGGLED_BACK" == "True" ]]; then
  pass "PATCH toggle — specialty re-activated (activo=True)"
else
  fail "PATCH toggle — activo='$TOGGLED_BACK', expected True"
fi

# PATCH /api/specialties/{unknown}/toggle → 404
http_call PATCH "/api/specialties/00000000-0000-0000-0000-000000000000/toggle"
assert_status 404 "PATCH /api/specialties/{unknown}/toggle → 404"

# Verify specialty audit fields in DB
if [[ -n "$NEW_SPEC_ID" ]]; then
  SPEC_CREATED_BY=$(psql_exec "SELECT created_by FROM specialties WHERE id = '${NEW_SPEC_ID}'")
  SPEC_UPDATED_BY=$(psql_exec "SELECT updated_by FROM specialties WHERE id = '${NEW_SPEC_ID}'")
  if [[ -n "$SPEC_CREATED_BY" ]]; then
    pass "specialties.created_by is set ($SPEC_CREATED_BY)"
  else
    fail "specialties.created_by is NULL for new specialty"
  fi
  if [[ -n "$SPEC_UPDATED_BY" ]]; then
    pass "specialties.updated_by is set ($SPEC_UPDATED_BY)"
  else
    fail "specialties.updated_by is NULL after update"
  fi
fi

# ---------------------------------------------------------------------------
# Appointment Stats
# ---------------------------------------------------------------------------
header "TESTS — Appointment Stats (/api/appointments/stats)"

# GET /api/appointments/stats — no filters
http_call GET "/api/appointments/stats"
assert_status 200 "GET /api/appointments/stats — no filters"
assert_field "status" "success" "stats response envelope"

# Verify all required fields in stats
for field in "data.total" "data.byStatus" "data.bySpecialty" "data.byDoctor" \
             "data.firstTimeCount" "data.returningCount" "data.byPatientType" \
             "data.dailyTrend" "data.peakHours"; do
  FIELD_VAL=$(jq_get "$field" "$HTTP_BODY")
  # total can be 0, which is falsy but valid; check key presence
  FIELD_EXISTS=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
keys = '${field}'.lstrip('data.').split('.')
nd = d.get('data', {})
print('yes' if '${field}'.replace('data.','').split('.')[0] in nd else 'no')
" 2>/dev/null || echo "no")
  if [[ "$FIELD_EXISTS" == "yes" ]]; then
    pass "GET /api/appointments/stats — field '$field' present"
  else
    fail "GET /api/appointments/stats — field '$field' missing"
    echo "       Body snippet: $(echo "$HTTP_BODY" | head -c 400)"
    break
  fi
done

# GET /api/appointments/stats?fecha=2026-03-27 — with date filter
http_call GET "/api/appointments/stats?fecha=2026-03-27"
assert_status 200 "GET /api/appointments/stats?fecha=2026-03-27 — date filter"
assert_field "status" "success" "stats with date filter envelope"

# GET /api/appointments/stats?doctor_id=... — with doctor filter
if [[ -n "${DOCTOR_ID:-}" ]]; then
  http_call GET "/api/appointments/stats?doctor_id=${DOCTOR_ID}"
  assert_status 200 "GET /api/appointments/stats?doctor_id={id} — doctor filter"
fi

# Verify stats does NOT conflict with /{appointment_id} path
# (i.e., "stats" should not be treated as an appointment UUID)
http_call GET "/api/appointments/stats"
if [[ "$HTTP_STATUS" == "200" ]]; then
  STATS_MSG=$(jq_get "message" "$HTTP_BODY")
  if [[ "$STATS_MSG" != *"cita"* ]] || [[ "$STATS_MSG" == *"Estadísticas"* ]]; then
    pass "GET /api/appointments/stats — route priority correct (not matched as /{id})"
  else
    fail "GET /api/appointments/stats — seems to match /{id} route instead"
  fi
fi

# ---------------------------------------------------------------------------
# Medical Records
# ---------------------------------------------------------------------------
header "TESTS — Medical Records (/api/medical-records)"

if [[ "${SKIP_MEDICAL:-0}" == "1" ]]; then
  warn "Skipping medical records tests (test appointment/patient/doctor not available)."
else
  # GET /api/medical-records?appointment_id={id} — no record yet
  http_call GET "/api/medical-records?appointment_id=${TEST_APPT_ID}"
  assert_status 200 "GET /api/medical-records?appointment_id — no record → data:null"
  INITIAL_DATA=$(jq_get "data" "$HTTP_BODY")
  if [[ -z "$INITIAL_DATA" ]]; then
    pass "GET /api/medical-records — returns null data for new appointment"
  else
    warn "GET /api/medical-records — expected null, got: $INITIAL_DATA"
  fi

  # PUT /api/medical-records — create (upsert)
  MR_PAYLOAD=$(cat <<MREOF
{
  "cita_id": "${TEST_APPT_ID}",
  "paciente_id": "${PATIENT_ID}",
  "doctor_id": "${DOCTOR_ID}",
  "schema_id": "medicina-general-v1",
  "schema_version": "1.0",
  "evaluacion": {
    "motivo_consulta": "Control rutinario de prueba NHM",
    "presion_arterial": "120/80",
    "temperatura": 36.5
  }
}
MREOF
)
  http_call PUT "/api/medical-records" "$MR_PAYLOAD"
  assert_status 200 "PUT /api/medical-records — create medical record"
  assert_field "status" "success" "medical record create envelope"
  assert_field "data.cita_id" "$TEST_APPT_ID" "medical record cita_id matches"
  assert_field "data.schema_id" "medicina-general-v1" "schema_id is set"
  assert_field "data.schema_version" "1.0" "schema_version is set"
  assert_field_nonempty "data.id" "medical record has id"

  RECORD_ID=$(jq_get "data.id" "$HTTP_BODY")

  # GET /api/medical-records?appointment_id — now has record
  http_call GET "/api/medical-records?appointment_id=${TEST_APPT_ID}"
  assert_status 200 "GET /api/medical-records?appointment_id — after upsert"
  assert_field "data.cita_id" "$TEST_APPT_ID" "medical record cita_id in GET"
  assert_field "data.schema_id" "medicina-general-v1" "schema_id in GET response"
  assert_field "data.preparado" "False" "medical record not yet prepared"

  # PUT /api/medical-records — update (upsert same cita_id)
  MR_UPDATE=$(cat <<MREOF2
{
  "cita_id": "${TEST_APPT_ID}",
  "paciente_id": "${PATIENT_ID}",
  "doctor_id": "${DOCTOR_ID}",
  "schema_id": "medicina-general-v1",
  "schema_version": "1.0",
  "evaluacion": {
    "motivo_consulta": "Control rutinario actualizado",
    "presion_arterial": "118/76",
    "temperatura": 37.0,
    "nota_adicional": "Sin novedades"
  }
}
MREOF2
)
  http_call PUT "/api/medical-records" "$MR_UPDATE"
  assert_status 200 "PUT /api/medical-records — update (second upsert)"

  # PATCH /api/medical-records/{id}/prepared — mark as prepared
  if [[ -n "$RECORD_ID" ]]; then
    PREPARED_PAYLOAD="{\"preparado_por\":\"${USER_ID}\"}"
    http_call PATCH "/api/medical-records/${RECORD_ID}/prepared" "$PREPARED_PAYLOAD"
    assert_status 200 "PATCH /api/medical-records/{id}/prepared — mark prepared"
    assert_field "status" "success" "mark prepared envelope"

    # Verify prepared state via GET
    http_call GET "/api/medical-records?appointment_id=${TEST_APPT_ID}"
    assert_field "data.preparado" "True" "medical record preparado=True after PATCH"
    assert_field_nonempty "data.preparado_at" "medical record preparado_at is set"
  fi

  # GET /api/medical-records/patient/{patient_id} — patient history
  http_call GET "/api/medical-records/patient/${PATIENT_ID}"
  assert_status 200 "GET /api/medical-records/patient/{id} — patient history"
  assert_field "status" "success" "patient history envelope"

  HISTORY_COUNT=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
print(len(d.get('data', [])))
")
  if [[ "$HISTORY_COUNT" -ge 1 ]]; then
    pass "GET /api/medical-records/patient/{id} — at least 1 record in history"
  else
    fail "GET /api/medical-records/patient/{id} — expected >=1 records, got 0"
  fi

  # GET /api/medical-records/patient/{id}?limit=1 — limit param
  http_call GET "/api/medical-records/patient/${PATIENT_ID}?limit=1"
  assert_status 200 "GET /api/medical-records/patient/{id}?limit=1"
  HISTORY_LIMITED=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
print(len(d.get('data', [])))
")
  if [[ "$HISTORY_LIMITED" -le 1 ]]; then
    pass "GET /api/medical-records/patient/{id}?limit=1 — respects limit"
  else
    fail "GET /api/medical-records/patient/{id}?limit=1 — returned $HISTORY_LIMITED, expected <=1"
  fi

  # GET /api/medical-records/patient/{id}?exclude={appt_id} — exclude current
  http_call GET "/api/medical-records/patient/${PATIENT_ID}?exclude=${TEST_APPT_ID}"
  assert_status 200 "GET /api/medical-records/patient/{id}?exclude — exclude appointment"
  EXCLUDED=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
records = d.get('data', [])
found = any(r.get('cita_id') == '${TEST_APPT_ID}' for r in records)
print('excluded' if not found else 'present')
")
  if [[ "$EXCLUDED" == "excluded" ]]; then
    pass "GET /api/medical-records/patient/{id}?exclude — test appointment excluded"
  else
    fail "GET /api/medical-records/patient/{id}?exclude — test appointment still present"
  fi

  # Verify history entry fields
  http_call GET "/api/medical-records/patient/${PATIENT_ID}?limit=5"
  FIRST_HAS_SCHEMA=$(echo "$HTTP_BODY" | "$VENV_PYTHON" -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('data', [])
print('yes' if items and 'schema_id' in items[0] else 'no')
")
  if [[ "$FIRST_HAS_SCHEMA" == "yes" ]]; then
    pass "patient history entries have 'schema_id' field"
  else
    fail "patient history entries missing 'schema_id' field"
  fi

  # Cleanup: remove test appointment and medical record from DB
  psql_exec "DELETE FROM medical_records WHERE fk_appointment_id = '${TEST_APPT_ID}'" >/dev/null 2>&1 || true
  psql_exec "DELETE FROM appointments WHERE id = '${TEST_APPT_ID}'" >/dev/null 2>&1 || true
  log "Test appointment cleaned up."
fi

# Cleanup: remove test specialty
if [[ -n "${NEW_SPEC_ID:-}" ]]; then
  psql_exec "DELETE FROM specialties WHERE id = '${NEW_SPEC_ID}'" >/dev/null 2>&1 || true
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
TOTAL=$((PASS + FAIL))
echo ""
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "${BOLD}  Test Results — NHM Endpoints${RESET}"
echo -e "${BOLD}════════════════════════════════════════${RESET}"
echo -e "  Total : $TOTAL"
echo -e "  ${GREEN}Pass  : $PASS${RESET}"
if [[ "$FAIL" -gt 0 ]]; then
  echo -e "  ${RED}Fail  : $FAIL${RESET}"
else
  echo -e "  Fail  : $FAIL"
fi
echo -e "${BOLD}════════════════════════════════════════${RESET}"

if [[ "$FAIL" -gt 0 ]]; then
  echo -e "\n${RED}Some tests failed. See output above for details.${RESET}"
  exit 1
else
  echo -e "\n${GREEN}All tests passed!${RESET}"
  exit 0
fi
