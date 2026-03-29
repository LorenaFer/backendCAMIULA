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
    -d '{"email":"admin@camiula.com","password":"admin123"}' \
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
E2E_CODE="MED-E2E-$(date +%s)"
NEW_MED="{\"code\":\"$E2E_CODE\",\"generic_name\":\"Paracetamol Test\",\"pharmaceutical_form\":\"Tabletas\",\"unit_measure\":\"Tabletas\",\"controlled_substance\":false,\"requires_refrigeration\":false}"
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
# 5. PURCHASE ORDERS — Recepción y control de lotes (PR #5)
# ═══════════════════════════════════════════════════════════════

echo "── Purchase Orders — Recepción ────────────────────────"

# 5.0 Crear orden de compra + ítems via script Python
echo -e "${YELLOW}  Creando orden de compra de prueba en BD...${NC}"

PO_SEED=$(python3 -c "
import asyncio, uuid, logging
logging.disable(logging.CRITICAL)
from datetime import date

async def seed():
    from app.shared.database.session import async_session_factory as async_session
    from app.modules.inventory.infrastructure.models import (
        PurchaseOrderModel, PurchaseOrderItemModel,
    )
    order_id = str(uuid.uuid4())
    item1_id = str(uuid.uuid4())
    item2_id = str(uuid.uuid4())
    async with async_session() as session:
        order = PurchaseOrderModel(
            id=order_id,
            fk_supplier_id='a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            order_number=f'OC-E2E-{order_id[:8]}',
            order_date=date.today(),
            order_status='sent',
            created_by='system',
        )
        session.add(order)
        await session.flush()
        items = [
            PurchaseOrderItemModel(
                id=item1_id,
                fk_purchase_order_id=order_id,
                fk_medication_id='d4e5f6a7-b8c9-0123-defa-234567890123',
                quantity_ordered=50,
                quantity_received=0,
                item_status='pending',
                created_by='system',
            ),
            PurchaseOrderItemModel(
                id=item2_id,
                fk_purchase_order_id=order_id,
                fk_medication_id='e5f6a7b8-c9d0-1234-efab-345678901234',
                quantity_ordered=30,
                quantity_received=0,
                item_status='pending',
                created_by='system',
            ),
        ]
        session.add_all(items)
        await session.commit()
    print(f'{order_id}|{item1_id}|{item2_id}')
asyncio.run(seed())
" 2>/dev/null || echo "")

PO_ID=$(echo "$PO_SEED" | cut -d'|' -f1)
PO_ITEM1_ID=$(echo "$PO_SEED" | cut -d'|' -f2)
PO_ITEM2_ID=$(echo "$PO_SEED" | cut -d'|' -f3)

if [ -z "$PO_ID" ]; then
  TOTAL=$((TOTAL + 1)); FAIL=$((FAIL + 1))
  echo -e "${RED}✗ FAIL${NC} No se pudo crear la orden de prueba (requiere BD activa)"
else
  echo -e "${GREEN}  Orden $PO_ID creada con 2 ítems.${NC}"

  # 5.1 Recepción parcial (solo ítem 1 — Ibuprofeno)
  RESULT=$(POST "/inventory/purchase-orders/$PO_ID/receive" "{
    \"items\": [{
      \"purchase_order_item_id\": \"$PO_ITEM1_ID\",
      \"quantity_received\": 50,
      \"lot_number\": \"LOT-E2E-IBU-001\",
      \"expiration_date\": \"2027-06-30\",
      \"unit_cost\": 1.25
    }]
  }")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /purchase-orders/:id/receive — recepción parcial" 200 "$STATUS" "$BODY"

  # 5.2 Verificar stock de Ibuprofeno subió
  IBU_ID="d4e5f6a7-b8c9-0123-defa-234567890123"
  RESULT=$(GET "/inventory/medications/$IBU_ID")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  IBU_STOCK=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['current_stock'])" 2>/dev/null || echo "0")
  TOTAL=$((TOTAL + 1))
  if [ "$IBU_STOCK" -ge 50 ]; then
    PASS=$((PASS + 1))
    echo -e "${GREEN}✓ PASS${NC} [stock=$IBU_STOCK] Ibuprofeno stock >= 50 tras recepción"
  else
    FAIL=$((FAIL + 1))
    echo -e "${RED}✗ FAIL${NC} [stock=$IBU_STOCK] Ibuprofeno stock esperado >= 50"
  fi

  # 5.3 Recepción completa (ítem 2 — Metformina)
  RESULT=$(POST "/inventory/purchase-orders/$PO_ID/receive" "{
    \"items\": [{
      \"purchase_order_item_id\": \"$PO_ITEM2_ID\",
      \"quantity_received\": 30,
      \"lot_number\": \"LOT-E2E-MET-001\",
      \"expiration_date\": \"2027-09-15\",
      \"unit_cost\": 0.85
    }]
  }")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /purchase-orders/:id/receive — recepción completa" 200 "$STATUS" "$BODY"

  # 5.4 Orden ya received — no puede re-recibirse (status invalido)
  RESULT=$(POST "/inventory/purchase-orders/$PO_ID/receive" "{
    \"items\": [{
      \"purchase_order_item_id\": \"$PO_ITEM1_ID\",
      \"quantity_received\": 10,
      \"lot_number\": \"LOT-EXTRA\",
      \"expiration_date\": \"2028-01-01\"
    }]
  }")
  STATUS=$(echo "$RESULT" | cut -d'|' -f1)
  BODY=$(echo "$RESULT" | cut -d'|' -f2-)
  assert_status "POST /receive — orden cerrada → 403" 403 "$STATUS" "$BODY"

  # 5.5 Item que no pertenece a la orden → 403 ITEM_NOT_IN_ORDER
  # Crear una segunda orden para obtener un item ajeno
  PO_SEED2=$(python3 -c "
import asyncio, uuid, logging
logging.disable(logging.CRITICAL)
from datetime import date
async def seed():
    from app.shared.database.session import async_session_factory as async_session
    from app.modules.inventory.infrastructure.models import (
        PurchaseOrderModel, PurchaseOrderItemModel,
    )
    oid = str(uuid.uuid4())
    iid = str(uuid.uuid4())
    async with async_session() as session:
        session.add(PurchaseOrderModel(
            id=oid,
            fk_supplier_id='a1b2c3d4-e5f6-7890-abcd-ef1234567890',
            order_number=f'OC-E2E2-{oid[:8]}',
            order_date=date.today(),
            order_status='sent',
            created_by='system',
        ))
        await session.flush()
        session.add(PurchaseOrderItemModel(
            id=iid,
            fk_purchase_order_id=oid,
            fk_medication_id='c3d4e5f6-a7b8-9012-cdef-123456789012',
            quantity_ordered=10,
            quantity_received=0,
            item_status='pending',
            created_by='system',
        ))
        await session.commit()
    print(f'{oid}|{iid}')
asyncio.run(seed())
" 2>/dev/null || echo "")

  PO2_ID=$(echo "$PO_SEED2" | cut -d'|' -f1)
  PO2_ITEM_ID=$(echo "$PO_SEED2" | cut -d'|' -f2)

  if [ -n "$PO2_ID" ] && [ -n "$PO2_ITEM_ID" ]; then
    # Intentar recibir item de orden 2 en orden 1 — debe fallar
    # (orden 1 ya está "received" así que dará 403 por status,
    #  pero el chequeo de ownership está antes del status check)
    # Probemos con la orden 2 en sí, enviando item de orden 1
    RESULT=$(POST "/inventory/purchase-orders/$PO2_ID/receive" "{
      \"items\": [{
        \"purchase_order_item_id\": \"$PO_ITEM1_ID\",
        \"quantity_received\": 5,
        \"lot_number\": \"LOT-FAKE\",
        \"expiration_date\": \"2028-01-01\"
      }]
    }")
    STATUS=$(echo "$RESULT" | cut -d'|' -f1)
    BODY=$(echo "$RESULT" | cut -d'|' -f2-)
    assert_status "POST /receive — item de otra orden → 403 ITEM_NOT_IN_ORDER" 403 "$STATUS" "$BODY"
  fi
fi

# 5.6 Orden inexistente
RESULT=$(POST "/inventory/purchase-orders/00000000-0000-0000-0000-000000000000/receive" '{"items":[{"purchase_order_item_id":"x","quantity_received":1,"lot_number":"L","expiration_date":"2028-01-01"}]}')
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /receive — orden inexistente → 404" 404 "$STATUS" "$BODY"

# 5.7 Body vacío (items=[]) → 422 (Pydantic min_length=1)
RESULT=$(POST "/inventory/purchase-orders/some-id/receive" '{"items":[]}')
STATUS=$(echo "$RESULT" | cut -d'|' -f1)
BODY=$(echo "$RESULT" | cut -d'|' -f2-)
assert_status "POST /receive — items vacío → 422" 422 "$STATUS" "$BODY"

echo ""

# ═══════════════════════════════════════════════════════════════
# 6. AUTH — Endpoints sin token deben fallar
# ═══════════════════════════════════════════════════════════════

echo "── Auth — Sin token ─────────────────────────────────"

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
