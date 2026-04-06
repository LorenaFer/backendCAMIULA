#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# E2E smoke test for Dashboard BI endpoints.
#
# Usage:
#   bash scripts/test_dashboard_e2e.sh [BASE_URL]
#
# Defaults to http://localhost:8000 if no BASE_URL is provided.
# Requires: curl, jq
# ─────────────────────────────────────────────────────────────
set -euo pipefail

BASE="${1:-http://localhost:8000}"
API="$BASE/api"
PASS=0
FAIL=0

# ── Helper ───────────────────────────────────────────────────

check() {
    local label="$1"
    local url="$2"
    local expected_status="${3:-200}"

    status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$url")
    if [ "$status" = "$expected_status" ]; then
        echo "  [PASS] $label  ($status)"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $label  (expected $expected_status, got $status)"
        FAIL=$((FAIL + 1))
    fi
}

# ── Authenticate ─────────────────────────────────────────────

EMAIL="e2e-dash-$(date +%s)@test.com"
PASSWORD="e2etest12345"

echo "==> Registering test user..."
curl -s -X POST "$API/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"full_name\":\"E2E Dashboard\",\"password\":\"$PASSWORD\"}" \
    > /dev/null

echo "==> Logging in..."
LOGIN_RESP=$(curl -s -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESP" | jq -r '.data.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "ERROR: Could not obtain JWT token."
    echo "$LOGIN_RESP"
    exit 1
fi
echo "  Token obtained."

# ── Run checks ───────────────────────────────────────────────

echo ""
echo "==> Testing Dashboard BI endpoints..."

check "GET /dashboard (day)"              "$API/dashboard?periodo=day"
check "GET /dashboard (month)"            "$API/dashboard?periodo=month"
check "GET /dashboard (year)"             "$API/dashboard?fecha=2026-01-01&periodo=year"
check "GET /medical-records/diagnostics/top" "$API/medical-records/diagnostics/top?limit=5"
check "GET /doctors/availability/summary" "$API/doctors/availability/summary"
check "GET /appointments/heatmap"         "$API/appointments/heatmap?fecha_desde=2026-01-01&fecha_hasta=2026-12-31"
check "GET /patients/demographics"        "$API/patients/demographics"

# ── Summary ──────────────────────────────────────────────────

echo ""
echo "==> Results: $PASS passed, $FAIL failed."
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All Dashboard BI smoke tests passed."
