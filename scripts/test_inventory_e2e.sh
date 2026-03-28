#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# E2E test script — Inventario module (PR #3)
#
# Requisitos:
#   1. Servidor corriendo:  uvicorn app.main:app --reload
#   2. Seeder ejecutado:    python -m app.shared.database.seeder inventory
#   3. Token JWT válido en la variable TOKEN (ver login abajo)
#
# Uso:
#   export TOKEN="<jwt>"
#   bash scripts/test_inventory_e2e.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

BASE="http://localhost:8000/api"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
TOTAL=0

# ─── Helpers ──────────────────────────────────────────────────

assert_status() {
  local test_name="$1"
  local expected="$2"
  local actual="$3"
  local body="$4"
  TOTAL=$((TOTAL + 1))

  if [ "$actual" -eq "$expected" ]; then
    echo -e "${GREEN}✓ PASS${NC} [$actual] $test_name"
    PASS=$((PASS + 1))
  else
    echo -e "${RED}✗ FAIL${NC} [$actual expected $expected] $test_name"
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

PUT() {
  local url="$1"
  local data="$2"
  local response
  response=$(curl -s -w "\n%{http_code}" -X PUT \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$data" \
    "$BASE$url")
  local body=$(echo "$response" | sed '$d')
  local status=$(echo "$response" | tail -1)
  echo "$status|$body"
}

DELETE() {
  local url="$1"
  local response
  response=$(curl -s -w "\n%{http_code}" -X DELETE \
    -H "Authorization: Bearer $TOKEN" "$BASE$url")
  local body=$(echo "$response" | sed '$d')
  local status=$(echo "$response" | tail -1)
  echo "$status|$body"
}

# ─── Pre-flight: obtener token ────────────────────────────────

if [ -z "${TOKEN:-}" ]; then
  echo -e "${YELLOW}TOKEN no definido. Intentando login con credenciales por defecto...${NC}"
  LOGIN_RESP=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@camiula.ula.ve","password":"admin123"}' \
    "$BASE/auth/login")
  LOGIN_STATUS=$(echo "$LOGIN_RESP" | tail -1)
  LOGIN_BODY=$(echo "$LOGIN_RESP" | sed '$d')

  if [ "$LOGIN_STATUS" -eq 200 ]; then
    TOKEN=$(echo "$LOGIN_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")
    if [ -n "$TOKEN" ]; then
      echo -e "${GREEN}Login exitoso.${NC}"
    else
      echo -e "${RED}No se pudo extraer el token del login. Exporta TOKEN manualmente.${NC}"
      exit 1
    fi
  else
    echo -e "${RED}Login fallido (status $LOGIN_STATUS). Exporta TOKEN manualmente.${NC}"
    echo "  Uso: export TOKEN=\"<jwt>\" && bash scripts/test_inventory_e2e.sh"
    exit 1
  fi
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo " E2E Tests — Módulo de Inventario"
echo "═══════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# 1. MEDICAMENTOS (CRUD)
# ═══════════════════════════════════════════════════════════════

echo "── Medicamentos ──────────────────────────────────────"

# 1.1 Listar medicamentos (seeder debe tener al menos 3)
RESULT=$(GET "/inventory/medications?page=1&page_size=20")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /medications — listar medicamentos" 200 "$STATUS" "$BODY"

# 1.2 Crear un medicamento nuevo
NEW_MED='{"code":"MED-TEST-E2E","generic_name":"Paracetamol Test","pharmaceutical_form":"Tabletas","unit_measure":"Tabletas","controlled_substance":false,"requires_refrigeration":false}'
RESULT=$(POST "/inventory/medications" "$NEW_MED")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /medications — crear medicamento" 201 "$STATUS" "$BODY"

# Extraer ID del medicamento creado
MED_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null || echo "")

# 1.3 Obtener medicamento por ID
if [ -n "$MED_ID" ]; then
  RESULT=$(GET "/inventory/medications/$MED_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "GET /medications/{id} — detalle de medicamento" 200 "$STATUS" "$BODY"
fi

# 1.4 Actualizar medicamento
if [ -n "$MED_ID" ]; then
  RESULT=$(PUT "/inventory/medications/$MED_ID" '{"commercial_name":"Paracetamol Plus E2E"}')
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "PUT /medications/{id} — actualizar medicamento" 200 "$STATUS" "$BODY"
fi

# 1.5 Buscar por nombre genérico
RESULT=$(GET "/inventory/medications?search=Amoxicilina")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /medications?search=Amoxicilina — búsqueda" 200 "$STATUS" "$BODY"

# 1.6 Filtrar por status
RESULT=$(GET "/inventory/medications?status=active")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /medications?status=active — filtro por status" 200 "$STATUS" "$BODY"

# 1.7 Opciones para selects
RESULT=$(GET "/inventory/medications/options")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /medications/options — lista simplificada" 200 "$STATUS" "$BODY"

# 1.8 Soft-delete medicamento de test
if [ -n "$MED_ID" ]; then
  RESULT=$(DELETE "/inventory/medications/$MED_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "DELETE /medications/{id} — soft-delete" 200 "$STATUS" "$BODY"
fi

# 1.9 Obtener medicamento eliminado (debe dar 404)
if [ -n "$MED_ID" ]; then
  RESULT=$(GET "/inventory/medications/$MED_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "GET /medications/{id} — 404 tras soft-delete" 404 "$STATUS" "$BODY"
fi

# 1.10 Código duplicado (debe dar 409 o 400)
DUP_MED='{"code":"MED-001","generic_name":"Duplicado","pharmaceutical_form":"Tabletas","unit_measure":"Tabletas","controlled_substance":false,"requires_refrigeration":false}'
RESULT=$(POST "/inventory/medications" "$DUP_MED")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
# Expect conflict (409) or internal error (500 if not handled)
if [ "$STATUS" -ge 400 ]; then
  TOTAL=$((TOTAL + 1)); PASS=$((PASS + 1))
  echo -e "${GREEN}✓ PASS${NC} [$STATUS] POST /medications — código duplicado rechazado"
else
  TOTAL=$((TOTAL + 1)); FAIL=$((FAIL + 1))
  echo -e "${RED}✗ FAIL${NC} [$STATUS] POST /medications — código duplicado debió fallar"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 2. VALIDACIÓN DE DESPACHO (lectura)
# ═══════════════════════════════════════════════════════════════

echo "── Despachos — Validación ────────────────────────────"

# Para este test necesitamos una prescripción en la BD.
# Si no existe, el endpoint retornará 404 y eso es correcto.

RESULT=$(GET "/inventory/dispatches/validate?prescription_id=nonexistent-rx&patient_type=all")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /dispatches/validate — receta inexistente → 404" 404 "$STATUS" "$BODY"

echo ""

# ═══════════════════════════════════════════════════════════════
# 3. DESPACHOS — Flujo de error
# ═══════════════════════════════════════════════════════════════

echo "── Despachos — Errores ────────────────────────────────"

# 3.1 Crear despacho con receta inexistente
RESULT=$(POST "/inventory/dispatches" '{"fk_prescription_id":"nonexistent-rx","patient_type":"all"}')
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /dispatches — receta inexistente → 404" 404 "$STATUS" "$BODY"

# 3.2 Obtener despacho inexistente
RESULT=$(GET "/inventory/dispatches/nonexistent-dispatch-id")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /dispatches/{id} — inexistente → 404" 404 "$STATUS" "$BODY"

# 3.3 Cancelar despacho inexistente
RESULT=$(POST "/inventory/dispatches/nonexistent-id/cancel" '{}')
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /dispatches/{id}/cancel — inexistente → 404" 404 "$STATUS" "$BODY"

# 3.4 Despachos de un paciente (vacío pero 200)
RESULT=$(GET "/inventory/dispatches/by-patient/patient-inexistente?page=1&page_size=10")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /dispatches/by-patient — paciente sin despachos → 200" 200 "$STATUS" "$BODY"

echo ""

# ═══════════════════════════════════════════════════════════════
# 4. REPORTES
# ═══════════════════════════════════════════════════════════════

echo "── Reportes ──────────────────────────────────────────"

# 4.1 Stock completo
RESULT=$(GET "/inventory/reports/stock")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/stock — reporte de stock" 200 "$STATUS" "$BODY"

# 4.2 Resumen ejecutivo
RESULT=$(GET "/inventory/reports/inventory-summary")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/inventory-summary — KPIs" 200 "$STATUS" "$BODY"

# 4.3 Stock bajo/crítico
RESULT=$(GET "/inventory/reports/low-stock")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/low-stock — alertas de stock" 200 "$STATUS" "$BODY"

# 4.4 Lotes próximos a vencer (default 90 días)
RESULT=$(GET "/inventory/reports/expiration?threshold_days=90")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/expiration — próximos a vencer" 200 "$STATUS" "$BODY"

# 4.5 Lotes próximos a vencer — horizontes 30/60/90
RESULT=$(GET "/inventory/reports/expiring-soon")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/expiring-soon — horizontes agrupados" 200 "$STATUS" "$BODY"

# 4.6 Consumo mensual
RESULT=$(GET "/inventory/reports/consumption?period=2026-03")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/consumption — consumo mensual" 200 "$STATUS" "$BODY"

# 4.7 Kardex/movimientos (necesitamos un medication_id del seeder)
MED_AMOX_ID="c3d4e5f6-a7b8-9012-cdef-123456789012"
RESULT=$(GET "/inventory/reports/movements?medication_id=$MED_AMOX_ID&page=1&page_size=20")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/movements — kardex de Amoxicilina" 200 "$STATUS" "$BODY"

# 4.8 Consumo con período inválido (debe dar 422)
RESULT=$(GET "/inventory/reports/consumption?period=invalid")
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "GET /reports/consumption?period=invalid — validación 422" 422 "$STATUS" "$BODY"

echo ""

# ═══════════════════════════════════════════════════════════════
# 5. AUTH — Endpoints sin token deben fallar
# ═══════════════════════════════════════════════════════════════

echo "── Auth — Sin token ──────────────────────────────────"

NO_AUTH_RESP=$(curl -s -w "\n%{http_code}" "$BASE/inventory/medications")
NO_AUTH_STATUS=$(echo "$NO_AUTH_RESP" | tail -1)
NO_AUTH_BODY=$(echo "$NO_AUTH_RESP" | sed '$d')

if [ "$NO_AUTH_STATUS" -eq 401 ] || [ "$NO_AUTH_STATUS" -eq 403 ]; then
  TOTAL=$((TOTAL + 1)); PASS=$((PASS + 1))
  echo -e "${GREEN}✓ PASS${NC} [$NO_AUTH_STATUS] GET /medications sin token → rechazado"
else
  TOTAL=$((TOTAL + 1)); FAIL=$((FAIL + 1))
  echo -e "${RED}✗ FAIL${NC} [$NO_AUTH_STATUS] GET /medications sin token debió dar 401/403"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════"
echo -e " Resultado: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC} de $TOTAL tests"
echo "═══════════════════════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
