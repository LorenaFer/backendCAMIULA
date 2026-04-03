#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# E2E smoke-test for the Patients module
# Usage:  bash scripts/test_patients_e2e.sh [BASE_URL]
# ──────────────────────────────────────────────────────────────

set -euo pipefail

API="${1:-http://localhost:8000}/api"
PASS=0
FAIL=0
CEDULA="V-E2E-$(date +%s)"

green()  { printf "\033[32m✔ %s\033[0m\n" "$1"; }
red()    { printf "\033[31m✘ %s\033[0m\n" "$1"; }
assert() {
    local label="$1" expected="$2" actual="$3"
    if [ "$actual" = "$expected" ]; then
        green "$label"; PASS=$((PASS+1))
    else
        red "$label  (expected=$expected, actual=$actual)"; FAIL=$((FAIL+1))
    fi
}

echo "═══════════════════════════════════════════"
echo "  Patients E2E — $API"
echo "═══════════════════════════════════════════"

# ── 0. Get auth token ─────────────────────────────────────────
echo ""
echo "▶ Getting auth token..."
E2E_EMAIL="e2e-patients-$(date +%s)@test.com"
E2E_PASS="pytest12345"

# Register a fresh user
curl -s -X POST "$API/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$E2E_EMAIL\",\"full_name\":\"E2E Patient Tester\",\"password\":\"$E2E_PASS\"}" > /dev/null 2>&1

# Login to get token
TOKEN=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$E2E_EMAIL\",\"password\":\"$E2E_PASS\"}" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('data',{}).get('access_token',''))
except:
    print('')
" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    red "Could not get token. Aborting."
    exit 1
fi
green "Token obtained"
AUTH="Authorization: Bearer $TOKEN"

# ── 1. GET /patients/max-nhm ──────────────────────────────────
echo ""
echo "▶ 1. GET /patients/max-nhm"
RESP=$(curl -s -w "\n%{http_code}" -H "$AUTH" "$API/patients/max-nhm")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert "Status 200" "200" "$CODE"
MAX_NHM=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['max_nhm'])" 2>/dev/null || echo "ERROR")
echo "  max_nhm=$MAX_NHM"

# ── 2. POST /patients (create) ───────────────────────────────
echo ""
echo "▶ 2. POST /patients — Create patient"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/patients" \
    -H "Content-Type: application/json" -H "$AUTH" \
    -d "{
        \"cedula\": \"$CEDULA\",
        \"first_name\": \"Test\",
        \"last_name\": \"E2E\",
        \"university_relation\": \"estudiante\",
        \"sex\": \"M\",
        \"phone\": \"0412-1234567\",
        \"medical_data\": {\"blood_type\": \"O+\"}
    }")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert "Status 201 (created)" "201" "$CODE"
PATIENT_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")
NHM=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['nhm'])" 2>/dev/null || echo "")
echo "  id=$PATIENT_ID, nhm=$NHM"

# ── 3. POST /patients — Duplicate (409) ──────────────────────
echo ""
echo "▶ 3. POST /patients — Duplicate cedula"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/patients" \
    -H "Content-Type: application/json" -H "$AUTH" \
    -d "{
        \"cedula\": \"$CEDULA\",
        \"first_name\": \"Other\",
        \"last_name\": \"Dup\",
        \"university_relation\": \"empleado\"
    }")
CODE=$(echo "$RESP" | tail -1)
assert "Status 409 (conflict)" "409" "$CODE"

# ── 4. GET /patients?cedula=X ────────────────────────────────
echo ""
echo "▶ 4. GET /patients?cedula=$CEDULA"
RESP=$(curl -s -w "\n%{http_code}" -H "$AUTH" "$API/patients?cedula=$CEDULA")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert "Status 200" "200" "$CODE"
FOUND_NAME=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['first_name'] if d else 'null')" 2>/dev/null || echo "ERROR")
assert "first_name = Test" "Test" "$FOUND_NAME"

# ── 5. GET /patients?nhm=X ───────────────────────────────────
echo ""
echo "▶ 5. GET /patients?nhm=$NHM"
RESP=$(curl -s -w "\n%{http_code}" -H "$AUTH" "$API/patients?nhm=$NHM")
CODE=$(echo "$RESP" | tail -1)
assert "Status 200" "200" "$CODE"

# ── 6. GET /patients/full?cedula=X ───────────────────────────
echo ""
echo "▶ 6. GET /patients/full?cedula=$CEDULA"
RESP=$(curl -s -w "\n%{http_code}" -H "$AUTH" "$API/patients/full?cedula=$CEDULA")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert "Status 200" "200" "$CODE"
HAS_DATA=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('yes' if d and 'medical_data' in d else 'no')" 2>/dev/null || echo "no")
assert "Includes medical_data" "yes" "$HAS_DATA"

# ── 7. GET /patients (paginated list) ────────────────────────
echo ""
echo "▶ 7. GET /patients (list)"
RESP=$(curl -s -w "\n%{http_code}" -H "$AUTH" "$API/patients?page=1&page_size=5")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
assert "Status 200" "200" "$CODE"
HAS_PAGINATION=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print('yes' if 'pagination' in d else 'no')" 2>/dev/null || echo "no")
assert "Paginated response" "yes" "$HAS_PAGINATION"

# ── 8. POST /patients/register ───────────────────────────────
echo ""
echo "▶ 8. POST /patients/register"
REG_CEDULA="V-REG-$(date +%s)"
RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/patients/register" \
    -H "Content-Type: application/json" -H "$AUTH" \
    -d "{
        \"cedula\": \"$REG_CEDULA\",
        \"first_name\": \"Portal\",
        \"last_name\": \"ULA\",
        \"university_relation\": \"estudiante\",
        \"phone\": \"0414-9876543\",
        \"sex\": \"F\",
        \"birth_date\": \"2000-05-15\",
        \"country\": \"Venezuela\",
        \"state_geo\": \"Merida\",
        \"city\": \"Merida\",
        \"blood_type\": \"A+\",
        \"allergies\": \"Penicilina, Polvo\"
    }")
CODE=$(echo "$RESP" | tail -1)
assert "Status 201 (register)" "201" "$CODE"

# ── 9. GET without auth (401/403) ────────────────────────────
echo ""
echo "▶ 9. GET /patients without token"
RESP=$(curl -s -w "\n%{http_code}" "$API/patients")
CODE=$(echo "$RESP" | tail -1)
if [ "$CODE" = "401" ] || [ "$CODE" = "403" ]; then
    green "Unauthenticated rejected ($CODE)"; PASS=$((PASS+1))
else
    red "Expected 401|403, got $CODE"; FAIL=$((FAIL+1))
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  Result: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
