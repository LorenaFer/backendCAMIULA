#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# E2E smoke test for Appointments module endpoints.
# Usage:  bash scripts/test_appointments_e2e.sh [BASE_URL]
# ─────────────────────────────────────────────────────────────
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

# ── Auth ──────────────────────────────────────────────────────
TS=$(date +%s)
EMAIL="e2e-appts-${TS}@test.com"
PASSWORD="e2eTest12345"

curl -s -o /dev/null -w '' "$API/auth/register" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"E2E Appts Tester\",\"password\":\"$PASSWORD\"}"

TOKEN=$(curl -s "$API/auth/login" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== Appointments Module E2E Smoke Tests ==="
echo ""

# ── Setup: create a patient ──────────────────────────────────
CEDULA="V-E2E-${TS}"
RESP=$(curl -s -w "\n%{http_code}" "$API/patients" \
  -X POST -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"cedula\":\"$CEDULA\",\"first_name\":\"E2EPaciente\",\"last_name\":\"ApptTest\",\"university_relation\":\"estudiante\"}")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "SETUP POST /patients" 201 "$STATUS"
PATIENT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# ── Setup: get a doctor ──────────────────────────────────────
RESP=$(curl -s -w "\n%{http_code}" "$API/doctors" -H "$AUTH")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
DOCTOR_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'] if d else '')" 2>/dev/null || echo "")
SPECIALTY_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['fk_specialty_id'] if d else '')" 2>/dev/null || echo "")

if [ -z "$DOCTOR_ID" ]; then
  echo "WARNING: No doctors found. Creating a specialty for basic tests."
  SPEC_RESP=$(curl -s -w "\n%{http_code}" "$API/specialties" \
    -X POST -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"name\":\"E2E-Spec-${TS}\"}")
  SPECIALTY_ID=$(echo "$SPEC_RESP" | sed '$d' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")
  DOCTOR_ID="00000000-0000-0000-0000-000000000000"
fi

echo ""
echo "--- Create Appointment ---"

# ── 1. POST /appointments ────────────────────────────────────
if [ -n "$PATIENT_ID" ] && [ -n "$DOCTOR_ID" ] && [ "$DOCTOR_ID" != "00000000-0000-0000-0000-000000000000" ]; then
  RESP=$(curl -s -w "\n%{http_code}" "$API/appointments" \
    -X POST -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"fk_patient_id\":\"$PATIENT_ID\",\"fk_doctor_id\":\"$DOCTOR_ID\",\"fk_specialty_id\":\"$SPECIALTY_ID\",\"appointment_date\":\"2026-06-15\",\"start_time\":\"10:${TS: -2}\",\"end_time\":\"11:00\",\"duration_minutes\":30,\"is_first_visit\":true,\"reason\":\"E2E test\"}")
  STATUS=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | sed '$d')
  assert_status "POST /appointments" 201 "$STATUS"
  APPT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")
else
  echo "  SKIP  POST /appointments (no valid doctor)"
  APPT_ID=""
fi

# ── 2. POST /appointments (double-booking) ───────────────────
if [ -n "$APPT_ID" ]; then
  RESP=$(curl -s -w "\n%{http_code}" "$API/appointments" \
    -X POST -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"fk_patient_id\":\"$PATIENT_ID\",\"fk_doctor_id\":\"$DOCTOR_ID\",\"fk_specialty_id\":\"$SPECIALTY_ID\",\"appointment_date\":\"2026-06-15\",\"start_time\":\"10:${TS: -2}\",\"end_time\":\"11:00\",\"duration_minutes\":30}")
  STATUS=$(echo "$RESP" | tail -1)
  assert_status "POST /appointments (double-booking)" 409 "$STATUS"
fi

echo ""
echo "--- List / Get ---"

# ── 3. GET /appointments ─────────────────────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments?page=1&page_size=5" -H "$AUTH")
assert_status "GET  /appointments (paginated)" 200 "$STATUS"

# ── 4. GET /appointments/{id} ────────────────────────────────
if [ -n "$APPT_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/$APPT_ID" -H "$AUTH")
  assert_status "GET  /appointments/{id}" 200 "$STATUS"
fi

# ── 5. GET /appointments?doctor_id=X&fecha=X&excluir_canceladas=true ──
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments?doctor_id=$DOCTOR_ID&fecha=2026-06-15&excluir_canceladas=true" -H "$AUTH")
assert_status "GET  /appointments (doctor day)" 200 "$STATUS"

# ── 6. GET /appointments?doctor_id=X&mes=2026-06&excluir_canceladas=true ──
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments?doctor_id=$DOCTOR_ID&mes=2026-06&excluir_canceladas=true" -H "$AUTH")
assert_status "GET  /appointments (doctor month)" 200 "$STATUS"

echo ""
echo "--- Status Update ---"

# ── 7. PATCH /appointments/{id}/status (valid) ───────────────
if [ -n "$APPT_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/$APPT_ID/status" \
    -X PATCH -H 'Content-Type: application/json' -H "$AUTH" \
    -d '{"new_status":"confirmada"}')
  assert_status "PATCH /appointments/{id}/status (pendiente->confirmada)" 200 "$STATUS"

  # ── 8. PATCH invalid transition ──────────────────────────────
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/$APPT_ID/status" \
    -X PATCH -H 'Content-Type: application/json' -H "$AUTH" \
    -d '{"new_status":"pendiente"}')
  assert_status "PATCH /appointments/{id}/status (invalid transition)" 400 "$STATUS"
fi

echo ""
echo "--- Stats / Check / Slots / Dates ---"

# ── 9. GET /appointments/stats ───────────────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/stats" -H "$AUTH")
assert_status "GET  /appointments/stats" 200 "$STATUS"

# ── 10. GET /appointments/check-slot ─────────────────────────
FAKE_DOC="00000000-0000-0000-0000-000000000000"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/check-slot?doctor_id=$FAKE_DOC&fecha=2026-12-01&hora_inicio=10:00" -H "$AUTH")
assert_status "GET  /appointments/check-slot" 200 "$STATUS"

# ── 11. GET /appointments/available-slots ─────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/available-slots?doctor_id=$FAKE_DOC&fecha=2026-12-01&es_nuevo=false" -H "$AUTH")
assert_status "GET  /appointments/available-slots" 200 "$STATUS"

# ── 12. GET /appointments/available-dates ─────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/available-dates?doctor_id=$FAKE_DOC&year=2026&month=12" -H "$AUTH")
assert_status "GET  /appointments/available-dates" 200 "$STATUS"

echo ""
echo "--- Unauthenticated ---"

# ── 13. Without token ────────────────────────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
  green "  PASS  GET /appointments without token (HTTP $STATUS)"
  PASS=$((PASS + 1))
else
  red   "  FAIL  GET /appointments without token  expected=401|403  got=$STATUS"
  FAIL=$((FAIL + 1))
fi

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/appointments/stats")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
  green "  PASS  GET /appointments/stats without token (HTTP $STATUS)"
  PASS=$((PASS + 1))
else
  red   "  FAIL  GET /appointments/stats without token  expected=401|403  got=$STATUS"
  FAIL=$((FAIL + 1))
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "=============================="
echo "  Passed: $PASS   Failed: $FAIL"
echo "=============================="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
