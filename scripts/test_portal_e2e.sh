#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# E2E smoke-test for the Patient Portal
# Usage:  bash scripts/test_portal_e2e.sh [BASE_URL]
# ──────────────────────────────────────────────────────────────

set -euo pipefail

API="${1:-http://localhost:8000}/api"
PASS=0
FAIL=0
CEDULA="V-PORTAL-$(date +%s)"

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
echo "  Patient Portal E2E — $API"
echo "═══════════════════════════════════════════"

# ── 0. Get auth token ─────────────────────────────────────────
echo ""
echo "▶ Getting auth token..."
E2E_EMAIL="e2e-portal-$(date +%s)@test.com"
E2E_PASS="pytest12345"

curl -s -X POST "$API/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$E2E_EMAIL\",\"full_name\":\"E2E Portal Tester\",\"password\":\"$E2E_PASS\"}" > /dev/null 2>&1

TOKEN=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$E2E_EMAIL\",\"password\":\"$E2E_PASS\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
echo "  Token obtained: ${TOKEN:0:20}..."

# ── 1. Register a patient (staff endpoint) ────────────────────
echo ""
echo "▶ 1. Register patient via staff endpoint..."
REG_RESP=$(curl -s -X POST "$API/patients" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"cedula\":\"$CEDULA\",\"first_name\":\"PortalE2E\",\"last_name\":\"Tester\",\"university_relation\":\"estudiante\"}")
REG_STATUS=$(echo "$REG_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
assert "Patient registered" "success" "$REG_STATUS"

PATIENT_NHM=$(echo "$REG_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['nhm'])")
PATIENT_ID=$(echo "$REG_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "  Patient NHM=$PATIENT_NHM ID=${PATIENT_ID:0:8}..."

# ── 2. Patient login by cedula (no auth required) ─────────────
echo ""
echo "▶ 2. Patient login by cedula..."
LOGIN_RESP=$(curl -s -X POST "$API/auth/patient/login" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"$CEDULA\",\"query_type\":\"cedula\"}")
LOGIN_FOUND=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['found'])")
assert "Login by cedula — found" "True" "$LOGIN_FOUND"

LOGIN_ID=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['patient']['id'])")
assert "Login by cedula — correct patient" "$PATIENT_ID" "$LOGIN_ID"

# ── 3. Patient login by NHM ───────────────────────────────────
echo ""
echo "▶ 3. Patient login by NHM..."
NHM_RESP=$(curl -s -X POST "$API/auth/patient/login" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"$PATIENT_NHM\",\"query_type\":\"nhm\"}")
NHM_FOUND=$(echo "$NHM_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['found'])")
assert "Login by NHM — found" "True" "$NHM_FOUND"

# ── 4. Patient not found ──────────────────────────────────────
echo ""
echo "▶ 4. Patient not found..."
NF_RESP=$(curl -s -X POST "$API/auth/patient/login" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"V-NONEXISTENT-000\",\"query_type\":\"cedula\"}")
NF_FOUND=$(echo "$NF_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['found'])")
assert "Not found — found=False" "False" "$NF_FOUND"

NF_PATIENT=$(echo "$NF_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['patient'])")
assert "Not found — patient=None" "None" "$NF_PATIENT"

# ── 5. No auth header needed ──────────────────────────────────
echo ""
echo "▶ 5. No auth header needed..."
NOAUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/auth/patient/login" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"V-ANYTHING\",\"query_type\":\"cedula\"}")
assert "No auth returns 200" "200" "$NOAUTH_CODE"

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════"
[ "$FAIL" -eq 0 ] || exit 1
