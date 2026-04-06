#!/usr/bin/env python3
"""Add docstrings to FastAPI endpoint functions that are missing them.

FastAPI uses the function docstring as the OpenAPI description field.
This script adds descriptions from a curated dictionary to all
endpoint functions missing docstrings.

Usage:
    python scripts/add_endpoint_docs.py
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOCS = {
    "patient_demographics": "Returns patient distribution statistics: count by university relation type (estudiante, personal, docente, familia, externo), count by sex, and first-time vs returning patient counts. Used by the dashboard.",
    "get_patient_full": "Retrieve complete patient data including medical_data (JSONB) and emergency_contact. Accepts one of three identifiers: `id` (UUID), `dni`, or `nhm`. Returns null if not found.",
    "get_max_nhm": "Returns the highest NHM (Hospital Medical Number) currently registered. Used by the registration form to display the next available NHM.",
    "list_or_search_patients": "Search and list patients with multiple strategies. Priority: nhm (exact) > dni (exact) > search (text) > list all. Text search queries dni, first_name, last_name, and NHM. Paginated, sorted by last_name.",
    "create_patient": "Register a new patient with auto-generated NHM. NHM assignment uses pg_advisory_xact_lock for concurrency safety. The dni must be unique.",
    "get_patient_by_id": "Retrieve a patient by their UUID. Returns 404 if not found.",
    "register_patient": "Self-registration endpoint for the ULA patient portal. No authentication required. Accepts extended fields (country, state, city, blood_type, emergency contact) that the backend composes into JSONB fields. Returns minimal data for security.",
    "get_my_profile": "Retrieve the authenticated user's profile including roles and permissions.",
    "update_my_profile": "Update the authenticated user's profile fields (full_name, phone).",
    "list_users": "List all users with optional filters. Supports pagination, role filtering, staff-only filter, and text search by name or email.",
    "create_user": "Create a staff user with specific roles (admin, doctor, analista, farmacia). If the doctor role is assigned, automatically creates a doctor record linked to the specified specialty.",
    "get_user": "Retrieve a specific user's profile by UUID, including roles and permissions.",
    "assign_role": "Assign an additional role to an existing user. The role must exist in the system.",
    "remove_role": "Remove a role from a user. The user must currently have the role assigned.",
    "get_doctor_options": "Lightweight doctor list optimized for dropdown selects. Returns id, name, specialty, and computed working days.",
    "list_doctors": "List all active doctors with their embedded specialty information.",
    "list_specialties": "List all medical specialties. Returns id, name, and active status.",
    "create_specialty": "Create a new medical specialty. The name must be unique.",
    "update_specialty": "Update an existing specialty's name or description.",
    "toggle_specialty": "Toggle a specialty's active/inactive status.",
    "availability_summary": "Aggregated availability summary grouped by specialty. Used by the dashboard.",
    "get_availability": "Get time blocks when a doctor is available on a specific day of the week. day_of_week: 1=Monday, 7=Sunday.",
    "create_availability": "Create a new availability time block for a doctor. Specify day_of_week (1-7), start_time, end_time (HH:MM), and slot_duration.",
    "update_availability": "Update an existing availability block's time range or slot duration.",
    "delete_availability": "Remove an availability block (hard delete, not soft-delete).",
    "get_exceptions": "Check if a doctor has a day-off exception on a specific date.",
    "get_heatmap": "Appointment frequency heatmap: count per day-of-week and hour. Filter by date range.",
    "get_stats": "Aggregated appointment statistics: counts by status, specialty, doctor, patient type, daily trend, and peak hours.",
    "check_slot": "Check if a specific time slot is already occupied. Returns occupied: true/false.",
    "get_available_slots": "Compute available time slots for a doctor on a date. Considers availability blocks, exceptions, and existing appointments. Duration: 60min for new patients, 30min for returning.",
    "get_available_dates": "List dates with availability in a given month. Excludes weekends, past dates, days without blocks, and days with exceptions.",
    "get_appointment": "Retrieve full appointment details including patient name, doctor name, and specialty.",
    "list_appointments": "List appointments with multiple view modes: doctor month view, doctor day view, or general list with search and pagination.",
    "create_appointment": "Create a new appointment. Validates no double-booking using SELECT FOR UPDATE.",
    "update_appointment_status": "Transition an appointment through the state machine. Valid: pendiente -> confirmada/cancelada/atendida/no_asistio, confirmada -> atendida/cancelada/no_asistio.",
    "top_diagnostics": "Top N most frequent diagnoses in a period. Extracts CIE-10 codes from medical record evaluations (JSONB).",
    "find_by_appointment": "Retrieve the medical record associated with a specific appointment.",
    "patient_history": "Patient's recent medical history. Returns the last N consultations with doctor, specialty, and evaluation data.",
    "upsert_record": "Create or update a medical record for an appointment. The evaluation field accepts flexible JSONB data.",
    "mark_prepared": "Mark a medical record as prepared by nursing staff.",
    "get_patient_orders": "List exam orders (lab tests, imaging) for a patient. Optionally filter by appointment_id.",
    "create_orders": "Create one or more exam orders for a consultation. The doctor_id is resolved from the appointment if not provided.",
    "list_schemas": "List all dynamic form schemas. Each schema defines form fields for medical record entry per specialty.",
    "get_schema": "Retrieve a form schema by specialty UUID or normalized name.",
    "upsert_schema": "Create or update a form schema for a specialty.",
    "delete_schema": "Soft-delete a form schema by specialty key name.",
    "list_categories": "List medication categories (antibiotic, analgesic, medical supplies, etc.). Supports text search.",
    "get_category": "Retrieve a medication category by UUID.",
    "create_category": "Create a new medication category. The name must be unique.",
    "update_category": "Update a medication category's name or description.",
    "delete_category": "Soft-delete a medication category.",
    "list_medications": "List medications with current stock levels computed from active batches. Supports search, status filter, therapeutic_class, and category_id.",
    "get_medication_options": "Simplified medication list for dropdown selects. Only active medications.",
    "get_medication": "Retrieve a medication's full details including real-time stock level and category.",
    "create_medication": "Register a new medication. The code must be unique. Optionally assign a category.",
    "update_medication": "Update medication catalog fields (PATCH semantics).",
    "delete_medication": "Soft-delete a medication from the catalog.",
    "list_suppliers": "List all suppliers with pagination including RIF, contact info, and payment terms.",
    "get_supplier_options": "Active suppliers for dropdown selects. Returns id, name, and RIF only.",
    "get_supplier": "Retrieve a supplier by UUID.",
    "create_supplier": "Register a new supplier. The RIF must be unique.",
    "update_supplier": "Update supplier information.",
    "list_purchase_orders": "List purchase orders with supplier info and item details. Ordered by creation date descending.",
    "get_purchase_order": "Retrieve a purchase order with items, supplier details, and traceability fields.",
    "create_purchase_order": "Create a purchase order in draft status. order_number is auto-generated.",
    "send_purchase_order": "Transition a purchase order from draft to sent. Records sent_at and sent_by.",
    "receive_purchase_order": "Register received items, creating batch records. Records inventory entry movements for traceability.",
    "list_batches": "List inventory batches with filters: medication_id, batch_status, expiring_before. Ordered by expiration date (FEFO).",
    "get_batch": "Retrieve a batch by UUID with lot details.",
    "list_prescriptions": "Search prescriptions by appointment_id, prescription_number, or patient_id. Includes item details with medication info.",
    "get_prescription": "Retrieve a prescription with all items and medication details.",
    "create_prescription": "Create a new prescription. prescription_number is auto-generated. fk_doctor_id resolved from appointment if not provided.",
    "list_dispatches": "List pharmacy dispatches with filters: patient_id, prescription_number, status, date range.",
    "validate_dispatch": "Pre-validate a dispatch. Checks stock (FEFO), monthly limits, and returns a detailed allocation plan.",
    "create_dispatch": "Execute a pharmacy dispatch using FEFO. Atomic: validates, allocates stock, checks limits, creates records, updates batches, records movements.",
    "get_by_prescription": "List all dispatches associated with a prescription.",
    "get_by_patient": "Paginated dispatch history for a patient.",
    "get_dispatch": "Retrieve a dispatch with item details and batch allocation.",
    "cancel_dispatch_endpoint": "Cancel a dispatch and revert stock to original batches.",
    "list_limits": "List monthly dispatch limits per medication, segmented by patient type.",
    "create_limit": "Create a monthly dispatch limit for a medication.",
    "update_limit": "Update a dispatch limit's max quantity or applies_to type.",
    "list_exceptions": "List authorized exceptions to dispatch limits.",
    "create_exception": "Create an exception allowing a patient to exceed the monthly limit.",
    "get_stock_report": "Consolidated stock report. Calculates stock_alert: ok (>50), low (<=50), critical (<=10), expired (0). Auto-generates stock alerts.",
    "get_inventory_summary": "Executive KPIs: total active SKUs, counts by alert level, total available units.",
    "get_low_stock": "Medications with stock_alert in low, critical, or expired. Ordered by criticality.",
    "get_expiration_report": "Batches expiring within threshold_days (default 90). Includes medication details.",
    "get_expiring_soon": "Batches expiring soon grouped into 30/60/90 day horizons.",
    "get_consumption_report": "Monthly consumption by medication for a period (YYYY-MM).",
    "get_movements": "Kardex: paginated entries + exits for a medication. Supports date range filters.",
    "get_inventory_movements": "All persisted inventory movements (entries, exits, adjustments, expirations).",
    "get_stock_alerts": "Persisted stock alerts with filters: status, level, medication_id.",
    "generate_stock_alerts": "Scan medications and generate alerts for those crossing stock thresholds. Auto-resolves when stock recovers.",
    "acknowledge_alert": "Mark a stock alert as acknowledged.",
    "resolve_alert": "Manually resolve a stock alert.",
    "get_dashboard": "Consolidated dashboard: KPIs, charts, trends. Aggregates cross-module data. Filterable by fecha and periodo.",
    "epi12_weekly_consolidation": "EPI-12: Weekly epidemiological consolidation by CIE-10, age group, and sex. O(k) where k = records in the week.",
    "epi13_nominal_listing": "EPI-13: Nominal listing of individual cases. Patient-level detail: name, age, sex, address, disease, CIE-10.",
    "epi15_monthly_morbidity": "EPI-15: Monthly morbidity by MPPS catalogue (~61 diseases, 10 categories). Monthly count + year-to-date accumulated.",
    "health_check": "Returns server status. Use to verify the API is running.",
}


def add_docstrings_to_file(filepath: Path) -> int:
    """Add docstrings to async def functions that lack them. Returns count added."""
    source = filepath.read_text()
    lines = source.split("\n")
    tree = ast.parse(source)

    insertions = []  # (line_number, indent, docstring)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        func_name = node.name
        if func_name not in DOCS:
            continue

        # Check if already has a docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Constant, ast.Str))):
            continue  # Already has docstring

        # Get the indentation of the function body
        first_body = node.body[0]
        body_line = lines[first_body.lineno - 1]
        indent = len(body_line) - len(body_line.lstrip())
        indent_str = " " * indent

        docstring = f'{indent_str}"""{DOCS[func_name]}"""'
        insertions.append((first_body.lineno - 1, docstring))

    if not insertions:
        return 0

    # Insert in reverse order to preserve line numbers
    for line_idx, docstring in sorted(insertions, reverse=True):
        lines.insert(line_idx, docstring)

    filepath.write_text("\n".join(lines))
    return len(insertions)


def main():
    total = 0
    for filepath in sorted(ROOT.rglob("app/modules/*/presentation/routes/*.py")):
        if filepath.name in ("__init__.py", "dependencies.py"):
            continue
        if ".claude" in str(filepath):
            continue
        try:
            count = add_docstrings_to_file(filepath)
            if count:
                print(f"  {filepath.relative_to(ROOT)}: +{count} docstrings")
                total += count
        except Exception as e:
            print(f"  ERROR {filepath.relative_to(ROOT)}: {e}")

    # Also handle main.py health check
    main_py = ROOT / "app" / "main.py"
    try:
        count = add_docstrings_to_file(main_py)
        if count:
            print(f"  app/main.py: +{count} docstrings")
            total += count
    except Exception:
        pass

    print(f"\nTotal: {total} docstrings added")

    # Verify no syntax errors
    errors = 0
    for filepath in ROOT.rglob("app/modules/*/presentation/routes/*.py"):
        if filepath.name in ("__init__.py", "dependencies.py"):
            continue
        if ".claude" in str(filepath):
            continue
        try:
            compile(filepath.read_text(), str(filepath), "exec")
        except SyntaxError as e:
            print(f"  SYNTAX ERROR: {filepath}: {e}")
            errors += 1

    if errors:
        print(f"\n{errors} files have syntax errors!")
        sys.exit(1)
    else:
        print("All files pass syntax check.")


if __name__ == "__main__":
    main()
