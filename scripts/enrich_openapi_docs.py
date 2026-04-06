#!/usr/bin/env python3
"""Enrich all FastAPI endpoint decorators with detailed OpenAPI descriptions.

Adds `description=` to every @router.get/post/patch/put/delete decorator
that is missing one. Descriptions follow Stripe/Twilio style: clear,
concise, mentions key parameters and business rules.

Usage:
    python scripts/enrich_openapi_docs.py          # Apply to all routers
    python scripts/enrich_openapi_docs.py --dry-run # Preview changes only
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════════════
# ENDPOINT DESCRIPTIONS — Stripe/Twilio style
# Key: (file_basename, summary_or_path_fragment) → description
# ═══════════════════════════════════════════════════════════

DESCRIPTIONS = {
    # ── AUTH ──────────────────────────────────────────────
    ("auth_routes.py", "/login"): (
        "Authenticate a user with email and password using the local auth provider. "
        "Returns a JWT access token valid for 30 minutes. "
        "Use the token in the `Authorization: Bearer <token>` header for protected endpoints."
    ),
    ("auth_routes.py", "/register"): (
        "Register a new user account. Assigns the `paciente` role by default. "
        "The email must be unique. Password must be at least 8 characters. "
        "Returns the created user profile with assigned roles."
    ),
    ("auth_routes.py", "/patient/login"): (
        "Authenticate a patient by dni or NHM without password. "
        "Used by the patient portal for quick access. "
        "Returns patient basic data if found, or `found: false` if not."
    ),

    # ── USERS ────────────────────────────────────────────
    ("user_routes.py", "/me\""):  (
        "Retrieve the authenticated user's profile including roles and permissions."
    ),
    ("user_routes.py", "update_my"):  (
        "Update the authenticated user's profile fields (full_name, phone). "
        "Only the user themselves can update their own profile."
    ),
    ("user_routes.py", "list_user"): (
        "List all users with optional filters. Supports pagination, role filtering, "
        "staff-only filter, and text search by name or email. "
        "Returns user profiles with their assigned roles."
    ),
    ("user_routes.py", "create_user"): (
        "Create a staff user with specific roles (admin, doctor, analista, farmacia). "
        "If the `doctor` role is assigned, automatically creates a doctor record "
        "linked to the specified specialty. Requires `users:create` permission."
    ),
    ("user_routes.py", "get_user"): (
        "Retrieve a specific user's profile by UUID, including roles and permissions."
    ),
    ("user_routes.py", "assign_role"): (
        "Assign an additional role to an existing user. "
        "The role must exist in the system. Duplicate assignments are ignored."
    ),
    ("user_routes.py", "remove_role"): (
        "Remove a role from a user. The user must currently have the role assigned."
    ),

    # ── PATIENTS ─────────────────────────────────────────
    ("patients_router.py", "demographics"): (
        "Returns patient distribution statistics: count by university relation type "
        "(estudiante, personal, docente, familia, externo), count by sex, "
        "and first-time vs returning patient counts. Used by the dashboard."
    ),
    ("patients_router.py", "full"): (
        "Retrieve complete patient data including medical_data (JSONB) and emergency_contact. "
        "Accepts one of three identifiers: `id` (UUID), `dni`, or `nhm`. "
        "Returns null if not found."
    ),
    ("patients_router.py", "max-nhm"): (
        "Returns the highest NHM (Hospital Medical Number) currently registered. "
        "Used by the registration form to display the next available NHM."
    ),
    ("patients_router.py", "list_or_search"): (
        "Search and list patients with multiple strategies. "
        "Priority: `nhm` (exact match) > `dni` (exact match) > `search` (text search) > list all. "
        "Text search queries dni, first_name, last_name, and NHM. "
        "Returns paginated results sorted by last_name."
    ),
    ("patients_router.py", "create_patient"): (
        "Register a new patient with auto-generated NHM (Hospital Medical Number). "
        "NHM assignment uses `pg_advisory_xact_lock` for concurrency safety. "
        "The dni must be unique. Returns the created patient with assigned NHM."
    ),
    ("patients_router.py", "get_patient_by"): (
        "Retrieve a patient by their UUID. Returns 404 if not found."
    ),
    ("patients_router.py", "register_patient"): (
        "Self-registration endpoint for the ULA patient portal. No authentication required. "
        "Accepts extended fields (country, state, city, blood_type, emergency contact) "
        "that the backend composes into JSONB fields. "
        "Returns minimal patient data (PatientPublicResponse) for security."
    ),

    # ── DOCTORS ──────────────────────────────────────────
    ("doctors_router.py", "options"): (
        "Lightweight doctor list optimized for dropdown selects. "
        "Returns id, name, specialty, and computed working days (DISTINCT day_of_week). "
        "Only includes active doctors."
    ),
    ("doctors_router.py", "list_doctor"): (
        "List all active doctors with their embedded specialty information. "
        "Uses joinedload for O(1) specialty resolution per doctor."
    ),

    # ── SPECIALTIES ──────────────────────────────────────
    ("specialties_router.py", "list_spec"): (
        "List all medical specialties. Returns id, name, and active status."
    ),
    ("specialties_router.py", "create_spec"): (
        "Create a new medical specialty. The name must be unique."
    ),
    ("specialties_router.py", "update_spec"): (
        "Update an existing specialty's name or description."
    ),
    ("specialties_router.py", "toggle"): (
        "Toggle a specialty's active/inactive status. "
        "Inactive specialties are hidden from dropdown selects but preserve historical data."
    ),

    # ── AVAILABILITY ─────────────────────────────────────
    ("availability_router.py", "summary"): (
        "Aggregated availability summary grouped by specialty. "
        "Shows total doctors, available slots, and occupation percentage per specialty. "
        "Used by the dashboard availability widget."
    ),
    ("availability_router.py", "get_avail"): (
        "Get time blocks when a doctor is available on a specific day of the week. "
        "Each block has start_time, end_time, and slot_duration (minutes). "
        "day_of_week uses ISO format: 1=Monday, 7=Sunday."
    ),
    ("availability_router.py", "create_avail"): (
        "Create a new availability time block for a doctor. "
        "Specify day_of_week (1-7), start_time, end_time (HH:MM), and slot_duration. "
        "Blocks cannot overlap for the same doctor and day."
    ),
    ("availability_router.py", "update_avail"): (
        "Update an existing availability block's time range or slot duration."
    ),
    ("availability_router.py", "delete_avail"): (
        "Remove an availability block. This is a hard delete (not soft-delete) "
        "since availability blocks are configuration, not transactional data."
    ),
    ("availability_router.py", "exception"): (
        "Check if a doctor has a day-off exception on a specific date. "
        "Returns the exception details if found, or empty list if the doctor is available."
    ),

    # ── APPOINTMENTS ─────────────────────────────────────
    ("appointments_router.py", "heatmap"): (
        "Appointment frequency heatmap: count of appointments per day-of-week and hour. "
        "Filter by date range. Used by the dashboard heatmap visualization."
    ),
    ("appointments_router.py", "stats"): (
        "Aggregated appointment statistics: counts by status, specialty, doctor, "
        "patient type, daily trend, and peak hours. "
        "Filterable by date, doctor_id, specialty, and status."
    ),
    ("appointments_router.py", "check-slot"): (
        "Check if a specific time slot is already occupied by another appointment. "
        "Returns `{occupied: true/false}`. Used before creating an appointment."
    ),
    ("appointments_router.py", "available-slots"): (
        "Compute available time slots for a doctor on a specific date. "
        "Considers the doctor's availability blocks, exceptions (days off), "
        "and existing appointments. Slot duration depends on `es_nuevo`: "
        "60 minutes for first-time patients, 30 minutes for returning patients."
    ),
    ("appointments_router.py", "available-dates"): (
        "List dates with availability in a given month for a doctor. "
        "Excludes weekends, past dates (< today + 2 days), days without "
        "availability blocks, and days with exceptions. Returns ISO date strings."
    ),
    ("appointments_router.py", "get_appointment"): (
        "Retrieve full appointment details including patient name, doctor name, "
        "and specialty. Returns 404 if not found."
    ),
    ("appointments_router.py", "list_appointment"): (
        "List appointments with multiple view modes: "
        "(1) Doctor month view: `doctor_id` + `mes=YYYY-MM`, "
        "(2) Doctor day view: `doctor_id` + `fecha`, "
        "(3) General list with search, pagination, and filters. "
        "The `q` parameter searches across patient name and dni."
    ),
    ("appointments_router.py", "create_appointment"): (
        "Create a new appointment. Validates no double-booking exists for "
        "the same doctor, date, and time slot using SELECT FOR UPDATE. "
        "Required: fk_patient_id, fk_doctor_id, appointment_date, start_time, end_time."
    ),
    ("appointments_router.py", "update_appointment"): (
        "Transition an appointment through the state machine. "
        "Valid transitions: pendiente -> confirmada/cancelada/atendida/no_asistio, "
        "confirmada -> atendida/cancelada/no_asistio. "
        "Invalid transitions return 400."
    ),

    # ── MEDICAL RECORDS ──────────────────────────────────
    ("medical_records_router.py", "top_diag"): (
        "Top N most frequent diagnoses in a period. "
        "Extracts CIE-10 codes from medical record evaluations (JSONB). "
        "Filterable by `periodo` (day/week/month/year) and `limit`."
    ),
    ("medical_records_router.py", "find_by_appointment"): (
        "Retrieve the medical record associated with a specific appointment. "
        "Returns null if no record exists yet for that appointment."
    ),
    ("medical_records_router.py", "patient_history"): (
        "Patient's recent medical history. Returns the last N consultations "
        "with doctor name, specialty, date, and evaluation data. "
        "Supports `exclude` param to omit the current record being edited."
    ),
    ("medical_records_router.py", "find_by_id"): (
        "Retrieve a medical record by its UUID."
    ),
    ("medical_records_router.py", "upsert"): (
        "Create or update a medical record for an appointment. "
        "If a record already exists for the appointment_id, it is updated. "
        "The evaluation field accepts flexible JSONB data matching the form schema."
    ),
    ("medical_records_router.py", "mark_prepared"): (
        "Mark a medical record as prepared by nursing staff. "
        "Sets the `is_prepared` flag to true. Used in the pre-consultation workflow."
    ),
    ("medical_records_router.py", "get_patient_orders"): (
        "List exam orders (lab tests, imaging, etc.) for a patient. "
        "Optionally filter by appointment_id. "
        "Returns order details: exam_name, status, doctor, and date."
    ),
    ("medical_records_router.py", "create_orders"): (
        "Create one or more exam orders for a consultation. "
        "Send an array of exams in the request body. "
        "The doctor_id is resolved from the appointment if not provided."
    ),

    # ── FORM SCHEMAS ─────────────────────────────────────
    ("schemas_router.py", "list_schemas"): (
        "List all dynamic form schemas. Each schema defines the form fields "
        "for medical record entry per specialty (e.g., general medicine, psychology)."
    ),
    ("schemas_router.py", "get_schema"): (
        "Retrieve a form schema by specialty UUID or normalized name. "
        "The schema contains sections with field definitions (type, label, required)."
    ),
    ("schemas_router.py", "upsert"): (
        "Create or update a form schema for a specialty. "
        "If a schema already exists for the specialty_id, it is replaced. "
        "The schema_json field contains the form structure with sections and fields."
    ),
    ("schemas_router.py", "delete"): (
        "Soft-delete a form schema by specialty key name. "
        "The schema is marked as deleted but can be recovered."
    ),

    # ── CATEGORIES ───────────────────────────────────────
    ("categories_router.py", "list_cat"): (
        "List medication categories (e.g., antibiotic, analgesic, medical supplies). "
        "Used to classify medications in the catalog. Supports text search by name."
    ),
    ("categories_router.py", "get_cat"): (
        "Retrieve a medication category by UUID."
    ),
    ("categories_router.py", "create_cat"): (
        "Create a new medication category. The name must be unique."
    ),
    ("categories_router.py", "update_cat"): (
        "Update a medication category's name or description."
    ),
    ("categories_router.py", "delete_cat"): (
        "Soft-delete a medication category. Medications linked to this category "
        "retain their fk_category_id but the category won't appear in lists."
    ),

    # ── MEDICATIONS ──────────────────────────────────────
    ("medications_router.py", "list_med"): (
        "List medications with current stock levels (computed from active batches). "
        "Supports search by generic_name, filter by status, therapeutic_class, "
        "and category_id. Stock is calculated in real-time from non-expired batches."
    ),
    ("medications_router.py", "options"): (
        "Simplified medication list for dropdown selects. "
        "Returns id, code, generic_name, pharmaceutical_form, unit_measure, and current_stock. "
        "Only active medications are included."
    ),
    ("medications_router.py", "get_med"): (
        "Retrieve a medication's full details including real-time stock level, "
        "category, and all catalog fields."
    ),
    ("medications_router.py", "create_med"): (
        "Register a new medication in the catalog. The code must be unique. "
        "Optionally assign a category via fk_category_id."
    ),
    ("medications_router.py", "update_med"): (
        "Update medication catalog fields. Only provided fields are updated (PATCH semantics)."
    ),
    ("medications_router.py", "delete_med"): (
        "Soft-delete a medication from the catalog. "
        "Existing batches and prescriptions referencing this medication are preserved."
    ),

    # ── SUPPLIERS ────────────────────────────────────────
    ("suppliers_router.py", "list_sup"): (
        "List all suppliers with pagination. "
        "Returns supplier profiles including RIF, contact info, and payment terms."
    ),
    ("suppliers_router.py", "option"): (
        "Active suppliers for dropdown selects. Returns id, name, and RIF only."
    ),
    ("suppliers_router.py", "get_sup"): (
        "Retrieve a supplier by UUID."
    ),
    ("suppliers_router.py", "create_sup"): (
        "Register a new supplier. The RIF must be unique."
    ),
    ("suppliers_router.py", "update_sup"): (
        "Update supplier information. Only provided fields are updated."
    ),

    # ── PURCHASE ORDERS ──────────────────────────────────
    ("purchase_orders_router.py", "list_pur"): (
        "List purchase orders with pagination. Includes supplier info and item details "
        "via joined relationships. Ordered by creation date descending."
    ),
    ("purchase_orders_router.py", "get_pur"): (
        "Retrieve a purchase order with all items, supplier details, and traceability "
        "fields (sent_at, sent_by, received_at, received_by)."
    ),
    ("purchase_orders_router.py", "create_pur"): (
        "Create a new purchase order in draft status. "
        "Include items with medication_id, quantity_ordered, and unit_cost. "
        "The order_number is auto-generated sequentially."
    ),
    ("purchase_orders_router.py", "send"): (
        "Transition a purchase order from draft to sent status. "
        "Records sent_at timestamp and sent_by user for traceability."
    ),
    ("purchase_orders_router.py", "receive"): (
        "Register received items for a purchase order. Creates batch records "
        "for each received item with lot_number, expiration_date, and quantity. "
        "Automatically records inventory entry movements for traceability. "
        "The order transitions to partial or received status based on completion."
    ),

    # ── BATCHES ──────────────────────────────────────────
    ("batches_router.py", "list_batch"): (
        "List inventory batches with optional filters: medication_id, batch_status "
        "(available/depleted/expired/quarantine), and expiring_before date. "
        "Ordered by expiration date ascending (FEFO)."
    ),
    ("batches_router.py", "get_batch"): (
        "Retrieve a batch by UUID with lot details: quantity_received, "
        "quantity_available, unit_cost, expiration_date, and batch_status."
    ),

    # ── PRESCRIPTIONS ────────────────────────────────────
    ("prescriptions_router.py", "list_presc"): (
        "Search prescriptions by appointment_id, prescription_number, or patient_id. "
        "Includes item details with medication info via joined relationships. "
        "Each item shows quantity_prescribed, quantity_dispatched, and item_status."
    ),
    ("prescriptions_router.py", "get_presc"): (
        "Retrieve a prescription with all items and medication details."
    ),
    ("prescriptions_router.py", "create_presc"): (
        "Create a new prescription for an appointment. "
        "The prescription_number is auto-generated. "
        "Include items with medication_id and quantity_prescribed. "
        "The fk_doctor_id is resolved from the appointment if not provided."
    ),

    # ── DISPATCHES ───────────────────────────────────────
    ("dispatches_router.py", "list_dispatch"): (
        "List pharmacy dispatches with filters: patient_id, prescription_number, "
        "status (pending/completed/cancelled), and date range. Paginated."
    ),
    ("dispatches_router.py", "validate"): (
        "Pre-validate a dispatch before execution. Checks stock availability "
        "using FEFO (First Expired, First Out) algorithm, verifies monthly "
        "dispatch limits per patient/medication, and returns a detailed plan."
    ),
    ("dispatches_router.py", "create_dispatch"): (
        "Execute a pharmacy dispatch using the FEFO algorithm. "
        "Atomically: (1) validates prescription, (2) allocates stock from oldest batches, "
        "(3) checks monthly limits, (4) creates dispatch + items, "
        "(5) updates batch quantities, (6) records inventory exit movements. "
        "Uses SELECT FOR UPDATE for concurrency safety."
    ),
    ("dispatches_router.py", "by-prescription"): (
        "List all dispatches associated with a prescription."
    ),
    ("dispatches_router.py", "by-patient"): (
        "Paginated dispatch history for a specific patient. "
        "Supports filters: prescription_number, status, date range."
    ),
    ("dispatches_router.py", "get_dispatch"): (
        "Retrieve a dispatch with all item details including batch allocation."
    ),
    ("dispatches_router.py", "cancel"): (
        "Cancel a completed dispatch and revert stock to the original batches. "
        "Restores quantity_available on each affected batch and updates "
        "prescription item status. Records reversal movements."
    ),

    # ── LIMITS ───────────────────────────────────────────
    ("limits_router.py", "list_limit"): (
        "List monthly dispatch limits per medication. "
        "Each limit defines the maximum quantity a patient can receive per month, "
        "segmented by patient type (all, student, employee, professor)."
    ),
    ("limits_router.py", "create_limit"): (
        "Create a monthly dispatch limit for a medication. "
        "Specify the medication_id, monthly_max_quantity, and applies_to type."
    ),
    ("limits_router.py", "update_limit"): (
        "Update a dispatch limit's maximum quantity or applies_to type."
    ),
    ("limits_router.py", "list_exception"): (
        "List authorized exceptions to dispatch limits. "
        "Exceptions allow specific patients to exceed the monthly limit "
        "for a medication within a date range."
    ),
    ("limits_router.py", "create_exception"): (
        "Create an exception to a dispatch limit for a specific patient. "
        "Requires: patient_id, medication_id, authorized_quantity, valid_from, "
        "valid_until, and reason for authorization."
    ),

    # ── INVENTORY REPORTS ────────────────────────────────
    ("reports_router.py", "inventory-movements"): (
        "Paginated list of all persisted inventory movements (entries, exits, "
        "adjustments, expirations). Each record includes medication, quantity, "
        "balance after movement, and reference to the source (batch, dispatch, PO)."
    ),
    ("reports_router.py", "stock-alerts"): (
        "List persisted stock alerts with filters: alert_status (active/resolved/acknowledged), "
        "alert_level (low/critical/expired), and medication_id. "
        "Includes active and resolved counts."
    ),
    ("reports_router.py", "acknowledge"): (
        "Mark a stock alert as acknowledged (user has seen it). "
        "Transitions from active to acknowledged status."
    ),
    ("reports_router.py", "resolve"): (
        "Manually resolve a stock alert. "
        "Alerts are also auto-resolved when stock recovers above threshold."
    ),

    # ── DASHBOARD ────────────────────────────────────────
    ("dashboard_router.py", "dashboard"): (
        "Consolidated dashboard with KPIs, charts, and trend data. "
        "Aggregates cross-module data: total patients, appointments today, "
        "pending/completed counts, top specialties, inventory alerts, "
        "and daily/weekly/monthly trends. "
        "Filterable by `fecha` (reference date) and `periodo` (day/week/month/year)."
    ),

    # ── EPI REPORTS ──────────────────────────────────────
    ("epi_router.py", "epi-12"): (
        "EPI-12: Weekly epidemiological consolidation by CIE-10 code, age group, and sex. "
        "Aggregates medical records within an ISO epidemiological week. "
        "Each disease shows distribution across 12 age groups (< 1, 1-4, ..., 65+) "
        "and by sex (H=male, M=female). O(k) where k = records in the week."
    ),
    ("epi_router.py", "epi-13"): (
        "EPI-13: Nominal listing of individual cases in an epidemiological week. "
        "Returns patient-level detail: name, age, sex, address, disease, and CIE-10 code. "
        "Used for case-by-case epidemiological investigation."
    ),
    ("epi_router.py", "epi-15"): (
        "EPI-15: Monthly morbidity consolidation by MPPS disease catalogue. "
        "Maps CIE-10 codes to the official Venezuelan Ministry of Health (MPPS) "
        "classification (~61 diseases across 10 categories). "
        "Shows monthly count and year-to-date accumulated totals per disease."
    ),
}


def find_and_add_descriptions(dry_run: bool = False):
    """Walk all router files and add descriptions where missing."""
    router_files = sorted(ROOT.rglob("app/modules/*/presentation/routes/*.py"))
    total_added = 0

    for filepath in router_files:
        if filepath.name in ("__init__.py", "dependencies.py"):
            continue

        content = filepath.read_text()
        original = content
        basename = filepath.name

        # Find all @router decorators
        # Pattern: @router.METHOD("path", ...)
        pattern = r'(@router\.(get|post|put|patch|delete)\([^)]*\))'

        for match in re.finditer(pattern, content, re.DOTALL):
            decorator = match.group(0)

            # Skip if already has description=
            if "description=" in decorator or "description =" in decorator:
                continue

            # Find matching description
            desc = None
            for (file_key, path_key), description in DESCRIPTIONS.items():
                if file_key == basename and path_key in decorator:
                    desc = description
                    break

            # Also try matching by the function name after the decorator
            if not desc:
                # Look at the function def after this decorator
                dec_end = match.end()
                func_match = re.search(r'async def (\w+)', content[dec_end:dec_end+200])
                if func_match:
                    func_name = func_match.group(1)
                    for (file_key, path_key), description in DESCRIPTIONS.items():
                        if file_key == basename and path_key in func_name:
                            desc = description
                            break

            if desc:
                # Insert description= before the closing )
                # Find the last ) of the decorator
                close_paren = decorator.rfind(")")
                if close_paren > 0:
                    inner = decorator[:close_paren].rstrip()
                    if inner.endswith(","):
                        new_dec = f'{inner}\n    description=(\n        "{desc}"\n    ),\n)'
                    else:
                        new_dec = f'{inner},\n    description=(\n        "{desc}"\n    ),\n)'
                    content = content.replace(decorator, new_dec, 1)
                    total_added += 1

        if content != original:
            if dry_run:
                print(f"  WOULD UPDATE {filepath.relative_to(ROOT)}")
            else:
                filepath.write_text(content)
                print(f"  UPDATED {filepath.relative_to(ROOT)}")

    return total_added


def main():
    parser = argparse.ArgumentParser(description="Enrich OpenAPI endpoint descriptions")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    args = parser.parse_args()

    print("Enriching OpenAPI endpoint descriptions...")
    count = find_and_add_descriptions(dry_run=args.dry_run)
    print(f"\n{'Would add' if args.dry_run else 'Added'} {count} descriptions.")

    if not args.dry_run and count > 0:
        print("\nRestart the server and check /redoc to verify.")


if __name__ == "__main__":
    main()
