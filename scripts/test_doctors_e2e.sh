#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# E2E smoke test for Doctors module endpoints.
# Usage:  bash scripts/test_doctors_e2e.sh [BASE_URL]
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
EMAIL="e2e-doctors-$(date +%s)@test.com"
PASSWORD="e2eTest12345"

curl -s -o /dev/null -w '' "$API/auth/register" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"full_name\":\"E2E Doctor Tester\",\"password\":\"$PASSWORD\"}"

TOKEN=$(curl -s "$API/auth/login" \
  -X POST -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo ""
echo "=== Doctors Module E2E Smoke Tests ==="
echo ""

# ── 1. GET /specialties ──────────────────────────────────────
echo "--- Specialties ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/specialties" -H "$AUTH")
assert_status "GET  /specialties" 200 "$STATUS"

# ── 2. POST /specialties ─────────────────────────────────────
SPEC_NAME="E2E-Spec-$(date +%s)"
RESP=$(curl -s -w "\n%{http_code}" "$API/specialties" \
  -X POST -H 'Content-Type: application/json' -H "$AUTH" \
  -d "{\"name\":\"$SPEC_NAME\"}")
STATUS=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert_status "POST /specialties" 201 "$STATUS"

SPEC_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# ── 3. PUT /specialties/{id} ─────────────────────────────────
if [ -n "$SPEC_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/specialties/$SPEC_ID" \
    -X PUT -H 'Content-Type: application/json' -H "$AUTH" \
    -d "{\"name\":\"Updated-$SPEC_NAME\"}")
  assert_status "PUT  /specialties/{id}" 200 "$STATUS"
fi

# ── 4. PATCH /specialties/{id}/toggle ─────────────────────────
if [ -n "$SPEC_ID" ]; then
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/specialties/$SPEC_ID/toggle" \
    -X PATCH -H "$AUTH")
  assert_status "PATCH /specialties/{id}/toggle" 200 "$STATUS"
fi

# ── 5. GET /doctors ──────────────────────────────────────────
echo ""
echo "--- Doctors ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors" -H "$AUTH")
assert_status "GET  /doctors" 200 "$STATUS"

# ── 6. GET /doctors/options ──────────────────────────────────
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors/options" -H "$AUTH")
assert_status "GET  /doctors/options" 200 "$STATUS"

# ── 7. GET /doctors/{id}/availability ────────────────────────
echo ""
echo "--- Availability ---"
FAKE_DOC_ID="00000000-0000-0000-0000-000000000000"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors/$FAKE_DOC_ID/availability" -H "$AUTH")
assert_status "GET  /doctors/{id}/availability" 200 "$STATUS"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors/$FAKE_DOC_ID/availability?dow=1" -H "$AUTH")
assert_status "GET  /doctors/{id}/availability?dow=1" 200 "$STATUS"

# ── 8. GET /doctors/{id}/exceptions ──────────────────────────
echo ""
echo "--- Exceptions ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors/$FAKE_DOC_ID/exceptions" -H "$AUTH")
assert_status "GET  /doctors/{id}/exceptions" 200 "$STATUS"

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/doctors/$FAKE_DOC_ID/exceptions?date=2026-01-15" -H "$AUTH")
assert_status "GET  /doctors/{id}/exceptions?date=..." 200 "$STATUS"

# ── 9. Unauthenticated ──────────────────────────────────────
echo ""
echo "--- Unauthenticated ---"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/specialties")
if [ "$STATUS" = "401" ] || [ "$STATUS" = "403" ]; then
  green "  PASS  GET /specialties without token (HTTP $STATUS)"
  PASS=$((PASS + 1))
else
  red   "  FAIL  GET /specialties without token  expected=401|403  got=$STATUS"
  FAIL=$((FAIL + 1))
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "=============================="
echo "  Passed: $PASS   Failed: $FAIL"
echo "=============================="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
