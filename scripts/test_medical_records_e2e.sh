#!/usr/bin/env bash
# -----------------------------------------------------------------
# E2E smoke test for Medical Records & Form Schemas endpoints.
# Usage:  bash scripts/test_medical_records_e2e.sh [BASE_URL]
# -----------------------------------------------------------------
set -euo pipefail

BASE="${1:-http://localhost:8000}"
API="$BASE/api"
PASS=0
FAIL=0

green()  { printf "\033[32m%s\033[0m\n" "$*"; }
red()    { printf "\033[31m%s\033[0m\n" "$*"; }

assert_status() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    green "  PASS  $label (HTTP $actual)"
    PASS=$((PASS + 1))
  else
    red   "  FAIL  $label  expected=$expected  got=$actual"
    FAIL=$((FAIL + 1))
  fi
}

# -- Auth ----------------------------------------------------------
TS=$(date +%s)
EMAIL="e2e-medrec-${TS}@test.com"
PASSWORD="e2eTest12345"

curl -s -o /dev/null -w '' "$API/auth/register" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"E2E MedRec Tester\",\"password\":\"$PASSWORD\"}"

TOKEN=$(curl -s "$API/auth/login" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== Medical Records & Form Schemas E2E Smoke Tests ==="
echo ""

# -- Setup: create a patient ---------------------------------------
CEDULA="V-E2E-MR-${TS}"
RESP=$(curl -s -w "\n%{http_code}" "$API/patients" \
  -X POST -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"cedula\":\"$CEDULA\",\"first_name\":\"E2EPaciente\",\"last_name\":\"MedRecTest\",\"university_relation\":\"estudiante\"}")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "SETUP POST /patients" 201 "$STATUS"
PATIENT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# -- Setup: get a doctor & specialty -------------------------------
RESP=$(curl -s -w "\n%{http_code}" "$API/doctors" -H "$AUTH")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
DOCTOR_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'] if d else '')" 2>/dev/null || echo "")
SPECIALTY_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['fk_specialty_id'] if d else '')" 2>/dev/null || echo "")

if [ -z "$DOCTOR_ID" ]; then
  echo "  WARNING: No doctors found. Using fake IDs for medical record tests."
  DOCTOR_ID="00000000-0000-0000-0000-000000000001"
  SPECIALTY_ID="00000000-0000-0000-0000-000000000002"
fi

# -- Setup: create an appointment (if real doctor) -----------------
APPT_ID=""
if [ "$DOCTOR_ID" != "00000000-0000-0000-0000-000000000001" ] && [ -n "$PATIENT_ID" ]; then
  RESP=$(curl -s -w "\n%{http_code}" "$API/appointments" \
    -X POST -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"fk_patient_id\":\"$PATIENT_ID\",\"fk_doctor_id\":\"$DOCTOR_ID\",\"fk_specialty_id\":\"$SPECIALTY_ID\",\"appointment_date\":\"2026-08-15\",\"start_time\":\"09:${TS: -2}\",\"end_time\":\"10:00\",\"duration_minutes\":30,\"is_first_visit\":true,\"reason\":\"E2E MedRec test\"}")
  STATUS=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | sed '$d')
  assert_status "SETUP POST /appointments" 201 "$STATUS"
  APPT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")
fi

# Use fake appointment ID if we couldn't create a real one
if [ -z "$APPT_ID" ]; then
  APPT_ID="fake-appt-${TS}"
fi

echo ""
echo "--- Medical Records: Upsert ---"

# 1. PUT /medical-records (create)
RESP=$(curl -s -w "\n%{http_code}" "$API/medical-records" \
  -X PUT -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"fk_appointment_id\":\"$APPT_ID\",\"fk_patient_id\":\"$PATIENT_ID\",\"fk_doctor_id\":\"$DOCTOR_ID\",\"evaluation\":{\"diagnosis\":{\"description\":\"Healthy\",\"code\":\"Z00\"},\"notes\":\"Initial visit\"}}")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "PUT /medical-records (create)" 201 "$STATUS"
RECORD_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# 2. PUT /medical-records (update same appointment)
RESP=$(curl -s -w "\n%{http_code}" "$API/medical-records" \
  -X PUT -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"fk_appointment_id\":\"$APPT_ID\",\"fk_patient_id\":\"$PATIENT_ID\",\"fk_doctor_id\":\"$DOCTOR_ID\",\"evaluation\":{\"diagnosis\":{\"description\":\"Updated diagnosis\",\"code\":\"Z00.1\"},\"notes\":\"Follow-up\"}}")
STATUS=$(echo "$RESP" | tail -1)
assert_status "PUT /medical-records (update)" 200 "$STATUS"

echo ""
echo "--- Medical Records: Query ---"

# 3. GET /medical-records?appointment_id=X
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records?appointment_id=$APPT_ID" -H "$AUTH")
assert_status "GET /medical-records?appointment_id=X" 200 "$STATUS"

# 4. GET /medical-records/{id}
if [ -n "$RECORD_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records/$RECORD_ID" -H "$AUTH")
  assert_status "GET /medical-records/{id}" 200 "$STATUS"
fi

# 5. GET /medical-records?appointment_id=nonexistent (404)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records?appointment_id=nonexistent-id" -H "$AUTH")
assert_status "GET /medical-records?appointment_id=nonexistent (404)" 404 "$STATUS"

# 6. GET /medical-records/patient/{patient_id}
if [ -n "$PATIENT_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records/patient/$PATIENT_ID?limit=5" -H "$AUTH")
  assert_status "GET /medical-records/patient/{patient_id}" 200 "$STATUS"
fi

echo ""
echo "--- Medical Records: Mark Prepared ---"

# 7. PATCH /medical-records/{id}/prepared
if [ -n "$RECORD_ID" ]; then
  RESP=$(curl -s -w "\n%{http_code}" "$API/medical-records/$RECORD_ID/prepared" \
    -X PATCH -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"prepared_by\":\"$DOCTOR_ID\"}")
  STATUS=$(echo "$RESP" | tail -1)
  assert_status "PATCH /medical-records/{id}/prepared" 200 "$STATUS"
fi

# 8. PATCH nonexistent (404)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records/nonexistent-id/prepared" \
  -X PATCH -H 'Content-Type: application/json' -H "$AUTH" \
  -d '{"prepared_by":"someone"}')
assert_status "PATCH /medical-records/{id}/prepared (404)" 404 "$STATUS"

echo ""
echo "--- Form Schemas ---"

# 9. PUT /schemas (create)
SCHEMA_SPEC_ID="$SPECIALTY_ID"
SCHEMA_NAME="Medicina General E2E ${TS}"
RESP=$(curl -s -w "\n%{http_code}" "$API/schemas" \
  -X PUT -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"specialty_id\":\"$SCHEMA_SPEC_ID\",\"specialty_name\":\"$SCHEMA_NAME\",\"version\":\"1.0\",\"schema_json\":{\"sections\":[{\"title\":\"Vitals\",\"fields\":[]}]}}")
STATUS=$(echo "$RESP" | tail -1)
assert_status "PUT /schemas (create)" 201 "$STATUS"

# 10. PUT /schemas (update)
RESP=$(curl -s -w "\n%{http_code}" "$API/schemas" \
  -X PUT -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"specialty_id\":\"$SCHEMA_SPEC_ID\",\"specialty_name\":\"$SCHEMA_NAME\",\"version\":\"2.0\",\"schema_json\":{\"sections\":[{\"title\":\"Vitals\",\"fields\":[\"BP\",\"HR\"]}]}}")
STATUS=$(echo "$RESP" | tail -1)
assert_status "PUT /schemas (update)" 200 "$STATUS"

# 11. GET /schemas
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/schemas" -H "$AUTH")
assert_status "GET /schemas (list all)" 200 "$STATUS"

# 12. GET /schemas/{specialty_id}
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/schemas/$SCHEMA_SPEC_ID" -H "$AUTH")
assert_status "GET /schemas/{specialty_id}" 200 "$STATUS"

# 13. GET /schemas/{normalized_name}
NORMALIZED=$(echo "$SCHEMA_NAME" | python3 -c "
import sys, unicodedata
name = sys.stdin.read().strip()
nfkd = unicodedata.normalize('NFKD', name)
ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
print(ascii_text.strip().lower().replace(' ', '-'))
")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/schemas/$NORMALIZED" -H "$AUTH")
assert_status "GET /schemas/{normalized_name}" 200 "$STATUS"

# 14. DELETE /schemas/{specialty_key}
RESP=$(curl -s -w "\n%{http_code}" "$API/schemas/$NORMALIZED" \
  -X DELETE -H "$AUTH")
STATUS=$(echo "$RESP" | tail -1)
assert_status "DELETE /schemas/{specialty_key}" 200 "$STATUS"

# 15. GET deleted schema (should be 404)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/schemas/$SCHEMA_SPEC_ID" -H "$AUTH")
assert_status "GET /schemas/{id} after delete (404)" 404 "$STATUS"

echo ""
echo "--- Unauthenticated ---"

# 16. Without token
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/medical-records?appointment_id=x")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
  green "  PASS  GET /medical-records without token (HTTP $STATUS)"
  PASS=$((PASS + 1))
else
  red   "  FAIL  GET /medical-records without token  expected=401|403  got=$STATUS"
  FAIL=$((FAIL + 1))
fi

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/schemas")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
  green "  PASS  GET /schemas without token (HTTP $STATUS)"
  PASS=$((PASS + 1))
else
  red   "  FAIL  GET /schemas without token  expected=401|403  got=$STATUS"
  FAIL=$((FAIL + 1))
fi

# -- Summary -------------------------------------------------------
echo ""
echo "=============================="
echo "  Passed: $PASS   Failed: $FAIL"
echo "=============================="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
