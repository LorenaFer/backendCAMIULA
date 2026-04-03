#!/usr/bin/env bash
# ===================================================================
# E2E smoke test — Pharmacy endpoints
#   (suppliers, prescriptions, batches, dispatch-limits, exceptions)
#
# Requirements:
#   1. Server running:  uvicorn app.main:app --reload
#   2. Seeder executed: python -m app.shared.database.seeder inventory
#   3. TOKEN env var or default login credentials
#
# Usage:
#   export TOKEN="<jwt>"
#   bash scripts/test_pharmacy_e2e.sh
# ===================================================================

set -euo pipefail

BASE="http://localhost:8000/api"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
TOTAL=0

# --- Helpers ------------------------------------------------------

assert_status() {
  local test_name="$1"
  local expected="$2"
  local actual="$3"
  local body="$4"
  TOTAL=$((TOTAL + 1))

  if [ "$actual" -eq "$expected" ]; then
    echo -e "${GREEN}  PASS${NC} [$actual] $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}  FAIL${NC} [$actual expected $expected] $test_name"
    echo "  Response: $(echo "$body" | head -c 300)"
    FAIL=$((FAIL + 1))
  fi
}

GET() {
  local url="$1"
  local response
  response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE$url")
  local body=$(echo "$response" | sed '$d')
  local status=$(echo "$response" | tail -1)
  echo "$status|$body"
}

POST() {
  local url="$1"
  local data="$2"
  local response
  response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$data" \
    "$BASE$url")
  local body=$(echo "$response" | sed '$d')
  local status=$(echo "$response" | tail -1)
  echo "$status|$body"
}

PATCH() {
  local url="$1"
  local data="$2"
  local response
  response=$(curl -s -w "\n%{http_code}" -X PATCH \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$data" \
    "$BASE$url")
  local body=$(echo "$response" | sed '$d')
  local status=$(echo "$response" | tail -1)
  echo "$status|$body"
}

extract_field() {
  python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])" 2>/dev/null <<< "$2" || echo ""
}

# --- Pre-flight: get token ----------------------------------------

if [ -z "${TOKEN:-}" ]; then
  echo -e "${YELLOW}TOKEN not set. Attempting default login...${NC}"
  LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@camiula.com","password":"admin123"}' \
    "$BASE/auth/login")
  LOGIN_STATUS=$(echo "$LOGIN_RESP" | tail -1)
  LOGIN_BODY=$(echo "$LOGIN_RESP" | sed '$d')

  if [ "$LOGIN_STATUS" -eq 200 ]; then
    TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
    if [ -n "$TOKEN" ]; then
      echo -e "${GREEN}Login successful.${NC}"
    else
      echo -e "${RED}Could not extract token. Export TOKEN manually.${NC}"
      exit 1
    fi
  else
    echo -e "${RED}Login failed (status $LOGIN_STATUS). Export TOKEN manually.${NC}"
    exit 1
  fi
fi

echo ""
echo "==================================================="
echo " E2E Smoke Tests — Pharmacy Endpoints"
echo "==================================================="
echo ""

# ===================================================================
# 1. SUPPLIERS
# ===================================================================

echo "-- Suppliers ------------------------------------------"

# 1.1 Create supplier
RIF="J-E2E-$(date +%s)"
RESULT=$(POST "/inventory/suppliers" "{\"name\":\"E2E Supplier\",\"rif\":\"$RIF\"}")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /suppliers -- create supplier" 201 "$STATUS" "$BODY"
SUPPLIER_ID=$(extract_field "id" "$BODY")

# 1.2 Get supplier by ID
if [ -n "$SUPPLIER_ID" ]; then
  RESULT=$(GET "/inventory/suppliers/$SUPPLIER_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "GET /suppliers/{id} -- get by ID" 200 "$STATUS" "$BODY"
fi

# 1.3 List suppliers
RESULT=$(GET "/inventory/suppliers?page=1&page_size=5")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /suppliers -- list paginated" 200 "$STATUS" "$BODY"

# 1.4 Supplier options
RESULT=$(GET "/inventory/suppliers/options")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /suppliers/options -- dropdown list" 200 "$STATUS" "$BODY"

# 1.5 Update supplier
if [ -n "$SUPPLIER_ID" ]; then
  RESULT=$(PATCH "/inventory/suppliers/$SUPPLIER_ID" '{"name":"E2E Supplier Updated"}')
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "PATCH /suppliers/{id} -- update" 200 "$STATUS" "$BODY"
fi

# 1.6 Duplicate RIF
RESULT=$(POST "/inventory/suppliers" "{\"name\":\"Dup\",\"rif\":\"$RIF\"}")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /suppliers -- duplicate RIF -> 409" 409 "$STATUS" "$BODY"

# 1.7 Not found
RESULT=$(GET "/inventory/suppliers/nonexistent-id")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /suppliers/{id} -- not found -> 404" 404 "$STATUS" "$BODY"

echo ""

# ===================================================================
# 2. PRESCRIPTIONS
# ===================================================================

echo "-- Prescriptions --------------------------------------"

# Create a medication first
MED_CODE="MED-E2E-$(date +%s)"
RESULT=$(POST "/inventory/medications" "{\"code\":\"$MED_CODE\",\"generic_name\":\"E2E Rx Med\",\"pharmaceutical_form\":\"Tablets\",\"unit_measure\":\"Tablets\",\"controlled_substance\":false,\"requires_refrigeration\":false}")
MED_BODY=$(echo "$RESULT" | cut -d'|' -f2-)
MED_ID=$(extract_field "id" "$MED_BODY")

APPT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
PATIENT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
DOCTOR_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

# 2.1 Create prescription
if [ -n "$MED_ID" ]; then
  RESULT=$(POST "/inventory/prescriptions" "{
    \"fk_appointment_id\": \"$APPT_ID\",
    \"fk_patient_id\": \"$PATIENT_ID\",
    \"fk_doctor_id\": \"$DOCTOR_ID\",
    \"items\": [{\"medication_id\": \"$MED_ID\", \"quantity_prescribed\": 10, \"dosage_instructions\": \"1 every 8h\"}]
  }")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /prescriptions -- create" 201 "$STATUS" "$BODY"
  RX_ID=$(extract_field "id" "$BODY")
fi

# 2.2 Get by ID
if [ -n "${RX_ID:-}" ]; then
  RESULT=$(GET "/inventory/prescriptions/$RX_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "GET /prescriptions/{id} -- get by ID" 200 "$STATUS" "$BODY"
fi

# 2.3 Search by appointment
RESULT=$(GET "/inventory/prescriptions?appointment_id=$APPT_ID")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /prescriptions?appointment_id -- search" 200 "$STATUS" "$BODY"

# 2.4 Search by patient
RESULT=$(GET "/inventory/prescriptions?patient_id=$PATIENT_ID")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /prescriptions?patient_id -- search" 200 "$STATUS" "$BODY"

# 2.5 Not found
RESULT=$(GET "/inventory/prescriptions/nonexistent-id")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /prescriptions/{id} -- not found -> 404" 404 "$STATUS" "$BODY"

echo ""

# ===================================================================
# 3. BATCHES
# ===================================================================

echo "-- Batches --------------------------------------------"

# 3.1 List batches
RESULT=$(GET "/inventory/batches?page=1&page_size=5")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /batches -- list paginated" 200 "$STATUS" "$BODY"

# 3.2 List with filters
RESULT=$(GET "/inventory/batches?status=available&page=1&page_size=10")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /batches?status=available -- filtered" 200 "$STATUS" "$BODY"

# 3.3 Not found
RESULT=$(GET "/inventory/batches/nonexistent-id")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /batches/{id} -- not found -> 404" 404 "$STATUS" "$BODY"

echo ""

# ===================================================================
# 4. DISPATCH LIMITS
# ===================================================================

echo "-- Dispatch Limits ------------------------------------"

# 4.1 Create limit
if [ -n "$MED_ID" ]; then
  RESULT=$(POST "/inventory/dispatch-limits" "{\"fk_medication_id\":\"$MED_ID\",\"monthly_max_quantity\":30,\"applies_to\":\"all\"}")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /dispatch-limits -- create" 201 "$STATUS" "$BODY"
  LIMIT_ID=$(extract_field "id" "$BODY")
fi

# 4.2 List limits
RESULT=$(GET "/inventory/dispatch-limits?page=1&page_size=5")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /dispatch-limits -- list" 200 "$STATUS" "$BODY"

# 4.3 Update limit
if [ -n "${LIMIT_ID:-}" ]; then
  RESULT=$(PATCH "/inventory/dispatch-limits/$LIMIT_ID" '{"monthly_max_quantity":50}')
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "PATCH /dispatch-limits/{id} -- update" 200 "$STATUS" "$BODY"
fi

# 4.4 Update not found
RESULT=$(PATCH "/inventory/dispatch-limits/nonexistent-id" '{"monthly_max_quantity":10}')
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "PATCH /dispatch-limits/{id} -- not found -> 404" 404 "$STATUS" "$BODY"

echo ""

# ===================================================================
# 5. DISPATCH EXCEPTIONS
# ===================================================================

echo "-- Dispatch Exceptions --------------------------------"

TODAY=$(date +%Y-%m-%d)
FUTURE=$(date -v+90d +%Y-%m-%d 2>/dev/null || date -d "+90 days" +%Y-%m-%d 2>/dev/null || echo "2026-07-01")

# 5.1 Create exception
if [ -n "$MED_ID" ]; then
  EXC_PATIENT=$(python3 -c "import uuid; print(uuid.uuid4())")
  RESULT=$(POST "/inventory/dispatch-exceptions" "{
    \"fk_patient_id\": \"$EXC_PATIENT\",
    \"fk_medication_id\": \"$MED_ID\",
    \"authorized_quantity\": 60,
    \"valid_from\": \"$TODAY\",
    \"valid_until\": \"$FUTURE\",
    \"reason\": \"E2E test chronic condition\"
  }")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /dispatch-exceptions -- create" 201 "$STATUS" "$BODY"
fi

# 5.2 List exceptions
RESULT=$(GET "/inventory/dispatch-exceptions?page=1&page_size=5")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /dispatch-exceptions -- list" 200 "$STATUS" "$BODY"

echo ""

# ===================================================================
# 6. AUTH — No-token requests must fail
# ===================================================================

echo "-- Auth (no token) ------------------------------------"

NO_AUTH=$(curl -s -w "\n%{http_code}" "$BASE/inventory/suppliers")
NO_AUTH_STATUS=$(echo "$NO_AUTH" | tail -1)
NO_AUTH_BODY=$(echo "$NO_AUTH" | sed '$d')
if [ "$NO_AUTH_STATUS" -eq 401 ] || [ "$NO_AUTH_STATUS" -eq 403 ]; then
  TOTAL=$((TOTAL + 1)); PASS=$((PASS + 1))
  echo -e "${GREEN}  PASS${NC} [$NO_AUTH_STATUS] GET /suppliers without token -> rejected"
else
  TOTAL=$((TOTAL + 1)); FAIL=$((FAIL + 1))
  echo -e "${RED}  FAIL${NC} [$NO_AUTH_STATUS] GET /suppliers without token should be 401/403"
fi

echo ""

# ===================================================================
# SUMMARY
# ===================================================================

echo "==================================================="
echo -e " Result: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC} of $TOTAL tests"
echo "==================================================="

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
