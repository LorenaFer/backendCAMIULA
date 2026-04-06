#!/usr/bin/env python3
"""Generate PDF: Patients Module API Documentation for CAMIULA thesis."""

import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from fpdf import FPDF

OUTPUT = ROOT / "docs" / "api" / "CAMIULA_Patients_Module.pdf"


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "CAMIULA  - Modulo de Pacientes", align="L")
        self.cell(0, 6, f"Rev. {date.today().isoformat()}", align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 100, 60)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 80, 50)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 100, 60)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def subsection(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def sub_subsection(self, title):
        self.set_font("Helvetica", "BI", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def code_block(self, text):
        self.set_font("Courier", "", 8.5)
        self.set_text_color(30, 30, 30)
        self.set_fill_color(245, 245, 245)
        self.set_draw_color(200, 200, 200)
        x = self.get_x()
        y = self.get_y()
        lines = text.strip().split("\n")
        h = len(lines) * 4.5 + 4
        if y + h > 270:
            self.add_page()
            y = self.get_y()
        self.rect(x, y, 190, h)
        self.set_xy(x + 2, y + 2)
        for line in lines:
            self.cell(186, 4.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 2)
        self.set_xy(x, y + h + 2)

    def bullet(self, text, bold_prefix=""):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.cell(5, 5.5, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 9.5)
            self.cell(self.get_string_width(bold_prefix) + 1, 5.5, bold_prefix)
            self.set_font("Helvetica", "", 9.5)
        self.multi_cell(175, 5.5, text)
        self.ln(0.5)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)

        self.set_font("Helvetica", "B", 8.5)
        self.set_fill_color(0, 80, 50)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(40, 40, 40)
        fill = False
        for row in rows:
            # Check page break
            if self.get_y() + 6.5 > 270:
                self.add_page()
                self.set_font("Helvetica", "B", 8.5)
                self.set_fill_color(0, 80, 50)
                self.set_text_color(255, 255, 255)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
                self.ln()
                self.set_font("Helvetica", "", 8.5)
                self.set_text_color(40, 40, 40)
                fill = False

            if fill:
                self.set_fill_color(235, 245, 240)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                align = "L" if i == 0 else "C"
                self.cell(col_widths[i], 6.5, str(cell), border=1,
                          fill=True, align=align)
            self.ln()
            fill = not fill
        self.ln(3)


def build():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ================================================================
    # PAGE 1  - Cover
    # ================================================================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 80, 50)
    pdf.cell(0, 15, "Modulo de Pacientes", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Documentacion Tecnica de API", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, "Centro Ambulatorio Medico Integral  - ULA", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    pdf.set_draw_color(0, 100, 60)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    info = [
        ("Proyecto", "Sistema de Gestion CAMIULA"),
        ("Backend", "FastAPI + SQLAlchemy 2.0 (async)"),
        ("Base de datos", "PostgreSQL 16"),
        ("Fecha", date.today().strftime("%d de %B de %Y")),
        ("Autores", "Nelson Vivas, Julio Vasquez"),
    ]
    for label, value in info:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, 7, f"{label}:", align="R")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"  {value}", new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    # PAGE 2  - Table of Contents
    # ================================================================
    pdf.add_page()
    pdf.section_title("Tabla de Contenidos")
    toc = [
        "1. Resumen del Modulo",
        "2. Modelo de Datos (tabla patients)",
        "3. Catalogo de Endpoints",
        "   3.1 GET /patients  - Listar y buscar pacientes",
        "   3.2 GET /patients/full  - Paciente completo",
        "   3.3 GET /patients/max-nhm  - Maximo NHM",
        "   3.4 GET /patients/{id}  - Paciente por ID",
        "   3.5 POST /patients  - Crear paciente",
        "   3.6 POST /patients/register  - Registro portal ULA",
        "   3.7 GET /patients/demographics  - Demografia",
        "4. Endpoints Relacionados en Otros Modulos",
        "   4.1 GET /medical-records/patient/{id}",
        "   4.2 GET /medical-records/orders/patient/{id}",
        "   4.3 GET /dashboard (seccion pacientes)",
        "5. Esquemas de Datos (Request/Response)",
        "6. Logica de Negocio Clave",
        "7. Autenticacion y Autorizacion",
    ]
    for item in toc:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, item, new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    # SECTION 1  - Resumen
    # ================================================================
    pdf.add_page()
    pdf.section_title("1. Resumen del Modulo")
    pdf.body(
        "El modulo de Pacientes gestiona el ciclo de vida completo del "
        "registro de pacientes en el Centro Ambulatorio Medico Integral de la "
        "Universidad de Los Andes (CAMIULA). Incluye el registro administrativo "
        "por personal del centro y el auto-registro a traves del portal ULA."
    )
    pdf.body(
        "Arquitectura: Clean Architecture con capas domain (entidades), "
        "application (DTOs, use cases), infrastructure (modelos SQLAlchemy, "
        "repositorios) y presentation (rutas FastAPI, schemas Pydantic)."
    )

    pdf.subsection("Estadisticas del modulo")
    pdf.add_table(
        ["Metrica", "Valor"],
        [
            ["Endpoints directos", "7"],
            ["Endpoints relacionados (otros modulos)", "3"],
            ["Total endpoints", "10"],
            ["Tabla principal", "patients"],
            ["Columnas en tabla", "25 + 7 audit"],
            ["Indices", "4 (nhm, cedula, last_name, university_relation)"],
        ],
        col_widths=[120, 70],
    )

    # ================================================================
    # SECTION 2  - Modelo de Datos
    # ================================================================
    pdf.add_page()
    pdf.section_title("2. Modelo de Datos  - Tabla patients")
    pdf.body(
        "Sigue el estandar de columnas del proyecto: "
        "id -> fk_* -> dominio -> patient_status -> status -> auditoria. "
        "Hereda de Base, SoftDeleteMixin y AuditMixin."
    )

    pdf.subsection("Columnas de la tabla")
    cols = [
        ["id", "String(36)", "PK", "UUID auto-generado"],
        ["fk_holder_patient_id", "String(36)", "FK nullable", "Paciente titular (dependientes)"],
        ["nhm", "Integer", "UNIQUE, idx", "Numero Historia Medica (secuencial)"],
        ["cedula", "String(20)", "UNIQUE, idx", "Cedula de identidad"],
        ["first_name", "String(100)", "NOT NULL", "Nombre"],
        ["last_name", "String(100)", "NOT NULL, idx", "Apellido"],
        ["sex", "String(1)", "nullable", "M / F"],
        ["birth_date", "Date", "nullable", "Fecha de nacimiento"],
        ["birth_place", "String(200)", "nullable", "Lugar de nacimiento"],
        ["marital_status", "String(20)", "nullable", "Estado civil"],
        ["religion", "String(100)", "nullable", "Religion"],
        ["origin", "String(200)", "nullable", "Procedencia"],
        ["home_address", "String(300)", "nullable", "Direccion habitacion"],
        ["phone", "String(20)", "nullable", "Telefono"],
        ["profession", "String(100)", "nullable", "Profesion"],
        ["current_occupation", "String(100)", "nullable", "Ocupacion actual"],
        ["work_address", "String(300)", "nullable", "Direccion trabajo"],
        ["economic_classif.", "String(50)", "nullable", "Clasificacion economica"],
        ["university_relation", "String(20)", "NOT NULL, idx", "Relacion con la ULA"],
        ["family_relationship", "String(20)", "nullable", "Parentesco con titular"],
        ["medical_data", "JSONB", "NOT NULL, def={}", "Datos medicos flexibles"],
        ["emergency_contact", "JSONB", "nullable", "Contacto de emergencia"],
        ["is_new", "Boolean", "NOT NULL, def=true", "Paciente primera vez"],
        ["patient_status", "String(30)", "NOT NULL, idx", "active/inactive/suspended"],
        ["status", "Enum(A/I/T)", "NOT NULL", "Control tecnico (mixin)"],
        ["created_at/by", "DateTime/Str", "audit", "Creacion"],
        ["updated_at/by", "DateTime/Str", "audit", "Edicion"],
        ["deleted_at/by", "DateTime/Str", "audit", "Soft-delete"],
    ]
    pdf.add_table(
        ["Columna", "Tipo", "Restriccion", "Descripcion"],
        cols,
        col_widths=[42, 30, 38, 80],
    )

    pdf.subsection("Campos JSONB: medical_data")
    pdf.code_block(
        '{\n'
        '  "blood_type": "O+",\n'
        '  "allergies": "Penicilina, Mariscos",\n'
        '  "medical_alerts": "Hipertenso, Diabetico"\n'
        '}'
    )

    pdf.subsection("Campos JSONB: emergency_contact")
    pdf.code_block(
        '{\n'
        '  "name": "Maria Gonzalez",\n'
        '  "relationship": "Esposa",\n'
        '  "phone": "0414-1234567",\n'
        '  "address": "Av. Universidad, Merida"\n'
        '}'
    )

    # ================================================================
    # SECTION 3  - Catalogo de Endpoints
    # ================================================================
    pdf.add_page()
    pdf.section_title("3. Catalogo de Endpoints")
    pdf.body("Base path: /api/patients. Todos los endpoints retornan el "
             "envelope estandar { status, message, data }.")

    # 3.1
    pdf.subsection("3.1 GET /api/patients  - Listar y buscar pacientes")
    pdf.body(
        "Endpoint principal de consulta. Soporta busqueda exacta por NHM o "
        "cedula, busqueda textual libre, y listado paginado."
    )
    pdf.sub_subsection("Query Parameters")
    pdf.add_table(
        ["Param", "Tipo", "Req", "Descripcion"],
        [
            ["nhm", "integer", "No", "Busqueda exacta por NHM"],
            ["cedula", "string", "No", "Busqueda exacta por cedula"],
            ["search", "string", "No", "Texto libre (cedula, nombre, NHM)"],
            ["page", "integer", "No", "Pagina (default: 1)"],
            ["page_size", "integer", "No", "Items por pagina (default: 20, max: 10000)"],
        ],
        col_widths=[25, 20, 12, 133],
    )
    pdf.sub_subsection("Logica de prioridad")
    pdf.bullet("Si se envia nhm: retorna un solo PatientPublicResponse (o null).", "nhm: ")
    pdf.bullet("Si se envia cedula: retorna un solo PatientPublicResponse (o null).", "cedula: ")
    pdf.bullet("Si se envia search: busqueda paginada por cedula, nombre o NHM.", "search: ")
    pdf.bullet("Sin filtros: lista paginada de todos los pacientes activos.", "default: ")

    pdf.sub_subsection("Response (paginado)")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "message": "Pacientes obtenidos exitosamente",\n'
        '  "data": {\n'
        '    "items": [ PatientResponse, ... ],\n'
        '    "pagination": {\n'
        '      "total": 250,\n'
        '      "page": 1,\n'
        '      "page_size": 20,\n'
        '      "total_pages": 13\n'
        '    }\n'
        '  }\n'
        '}'
    )

    # 3.2
    pdf.subsection("3.2 GET /api/patients/full  - Paciente completo")
    pdf.body("Retorna todos los campos del paciente. Acepta uno de tres "
             "identificadores como query param.")
    pdf.add_table(
        ["Param", "Tipo", "Descripcion"],
        [
            ["id", "string (UUID)", "ID del paciente"],
            ["cedula", "string", "Cedula de identidad"],
            ["nhm", "integer", "Numero historia medica"],
        ],
        col_widths=[30, 40, 120],
    )
    pdf.sub_subsection("Response")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "data": {\n'
        '    "id": "uuid", "nhm": 1234, "cedula": "V-12345678",\n'
        '    "first_name": "Juan", "last_name": "Perez",\n'
        '    "sex": "M", "birth_date": "1990-05-15",\n'
        '    "medical_data": { "blood_type": "O+", ... },\n'
        '    "emergency_contact": { "name": "...", ... },\n'
        '    "is_new": false, "created_at": "2026-01-15T...",\n'
        '    ... (todos los campos)\n'
        '  }\n'
        '}'
    )

    # 3.3
    pdf.subsection("3.3 GET /api/patients/max-nhm  - Maximo NHM")
    pdf.body("Retorna el NHM mas alto registrado en la base de datos. "
             "Util para mostrar en la interfaz el proximo NHM a asignar.")
    pdf.sub_subsection("Response")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "data": { "max_nhm": 1250 }\n'
        '}'
    )

    # 3.4
    pdf.subsection("3.4 GET /api/patients/{patient_id}  - Paciente por ID")
    pdf.body("Busqueda directa por UUID. Retorna PatientResponse completo "
             "o 404 si no existe.")
    pdf.code_block(
        'GET /api/patients/a1b2c3d4-e5f6-7890-abcd-1234567890ab\n'
        '\n'
        'Response: PatientResponse | 404 NotFoundException'
    )

    # 3.5
    if pdf.get_y() > 200:
        pdf.add_page()
    pdf.subsection("3.5 POST /api/patients  - Crear paciente (admin/staff)")
    pdf.body("Crea un paciente con NHM auto-generado. Requiere autenticacion. "
             "El NHM se asigna de forma atomica usando pg_advisory_xact_lock "
             "para evitar race conditions en concurrencia.")
    pdf.sub_subsection("Request Body: PatientCreate")
    pdf.add_table(
        ["Campo", "Tipo", "Req", "Descripcion"],
        [
            ["cedula", "string", "Si", "Cedula unica"],
            ["first_name", "string", "Si", "Nombre"],
            ["last_name", "string", "Si", "Apellido"],
            ["university_relation", "string", "Si", "estudiante/personal/familia/externo"],
            ["sex", "string", "No", "M o F"],
            ["birth_date", "string", "No", "YYYY-MM-DD"],
            ["birth_place", "string", "No", "Lugar de nacimiento"],
            ["home_address", "string", "No", "Direccion"],
            ["phone", "string", "No", "Telefono"],
            ["medical_data", "object", "No", "{ blood_type, allergies, ... }"],
            ["emergency_contact", "object", "No", "{ name, phone, relationship, ... }"],
            ["... (13 campos mas)", "", "No", "Ver esquema completo en seccion 5"],
        ],
        col_widths=[42, 20, 12, 116],
    )
    pdf.sub_subsection("Response (201 Created)")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "message": "Paciente creado exitosamente",\n'
        '  "data": { ...PatientResponse (nhm auto-asignado) }\n'
        '}'
    )

    # 3.6
    pdf.add_page()
    pdf.subsection("3.6 POST /api/patients/register  - Registro portal ULA")
    pdf.body(
        "Endpoint publico para auto-registro desde el portal de la ULA. "
        "No requiere autenticacion. Acepta campos extendidos que el backend "
        "compone en los campos JSONB (medical_data, emergency_contact)."
    )
    pdf.sub_subsection("Request Body: PatientRegister (campos adicionales)")
    pdf.add_table(
        ["Campo", "Tipo", "Req", "Composicion backend"],
        [
            ["country", "string", "No", "-> birth_place"],
            ["state_geo", "string", "No", "-> birth_place"],
            ["city", "string", "No", "-> birth_place"],
            ["blood_type", "string", "No", "-> medical_data.blood_type"],
            ["allergies", "string", "No", "-> medical_data.allergies"],
            ["medical_alerts", "string", "No", "-> medical_data.medical_alerts"],
            ["emergency_name", "string", "No", "-> emergency_contact.name"],
            ["emergency_relationship", "string", "No", "-> emergency_contact.relationship"],
            ["emergency_phone", "string", "No", "-> emergency_contact.phone"],
            ["emergency_address", "string", "No", "-> emergency_contact.address"],
            ["holder_cedula", "string", "No", "-> lookup fk_holder_patient_id"],
            ["email", "string", "No", "Almacenado para referencia"],
        ],
        col_widths=[45, 18, 12, 115],
    )
    pdf.sub_subsection("Response (201 Created)  - PatientPublicResponse")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "message": "Paciente registrado exitosamente",\n'
        '  "data": {\n'
        '    "id": "uuid",\n'
        '    "nhm": 1251,\n'
        '    "first_name": "Maria",\n'
        '    "last_name": "Garcia",\n'
        '    "university_relation": "estudiante",\n'
        '    "is_new": true\n'
        '  }\n'
        '}'
    )

    # 3.7
    pdf.subsection("3.7 GET /api/patients/demographics  - Demografia")
    pdf.body("Retorna estadisticas de distribucion de pacientes. "
             "Utilizado por el dashboard del sistema.")
    pdf.sub_subsection("Response")
    pdf.code_block(
        '{\n'
        '  "status": "success",\n'
        '  "data": {\n'
        '    "patients_by_type": {\n'
        '      "estudiante": 150, "personal": 45,\n'
        '      "familia": 30, "externo": 25\n'
        '    },\n'
        '    "patients_by_sex": { "M": 120, "F": 110, "N/D": 20 },\n'
        '    "first_time_count": 80,\n'
        '    "returning_count": 170\n'
        '  }\n'
        '}'
    )

    # ================================================================
    # SECTION 4  - Endpoints relacionados
    # ================================================================
    pdf.add_page()
    pdf.section_title("4. Endpoints Relacionados en Otros Modulos")

    pdf.subsection("4.1 GET /api/medical-records/patient/{patient_id}")
    pdf.body("Historial medico del paciente. Retorna las ultimas N consultas "
             "con doctor, especialidad y diagnostico.")
    pdf.add_table(
        ["Param", "Tipo", "Req", "Descripcion"],
        [
            ["patient_id", "string (path)", "Si", "UUID del paciente"],
            ["limit", "integer (query)", "No", "Cantidad de registros (default: 5, max: 50)"],
            ["exclude", "string (query)", "No", "ID de registro a excluir"],
        ],
        col_widths=[30, 35, 12, 113],
    )

    pdf.subsection("4.2 GET /api/medical-records/orders/patient/{patient_id}")
    pdf.body("Ordenes de examenes medicos del paciente. Filtrable por cita.")
    pdf.add_table(
        ["Param", "Tipo", "Req", "Descripcion"],
        [
            ["patient_id", "string (path)", "Si", "UUID del paciente"],
            ["appointment_id", "string (query)", "No", "Filtrar por cita especifica"],
        ],
        col_widths=[30, 35, 12, 113],
    )

    pdf.subsection("4.3 GET /api/dashboard  - Seccion de pacientes")
    pdf.body("El dashboard consolidado incluye KPIs de pacientes: total "
             "activos, nuevos vs recurrentes, distribucion por tipo y sexo.")

    # ================================================================
    # SECTION 5  - Esquemas
    # ================================================================
    pdf.add_page()
    pdf.section_title("5. Esquemas de Datos (Request / Response)")

    pdf.subsection("PatientResponse (respuesta completa)")
    pdf.code_block(
        '{\n'
        '  "id": "string (UUID)",\n'
        '  "nhm": "integer",\n'
        '  "cedula": "string",\n'
        '  "first_name": "string",\n'
        '  "last_name": "string",\n'
        '  "sex": "string | null",\n'
        '  "birth_date": "string (YYYY-MM-DD) | null",\n'
        '  "birth_place": "string | null",\n'
        '  "marital_status": "string | null",\n'
        '  "religion": "string | null",\n'
        '  "origin": "string | null",\n'
        '  "home_address": "string | null",\n'
        '  "phone": "string | null",\n'
        '  "profession": "string | null",\n'
        '  "current_occupation": "string | null",\n'
        '  "work_address": "string | null",\n'
        '  "economic_classification": "string | null",\n'
        '  "university_relation": "string",\n'
        '  "family_relationship": "string | null",\n'
        '  "fk_holder_patient_id": "string | null",\n'
        '  "medical_data": "object",\n'
        '  "emergency_contact": "object | null",\n'
        '  "is_new": "boolean",\n'
        '  "created_at": "string (ISO datetime)"\n'
        '}'
    )

    pdf.subsection("PatientPublicResponse (respuesta publica/reducida)")
    pdf.code_block(
        '{\n'
        '  "id": "string (UUID)",\n'
        '  "nhm": "integer",\n'
        '  "first_name": "string",\n'
        '  "last_name": "string",\n'
        '  "university_relation": "string",\n'
        '  "is_new": "boolean"\n'
        '}'
    )

    # ================================================================
    # SECTION 6  - Logica de Negocio
    # ================================================================
    pdf.add_page()
    pdf.section_title("6. Logica de Negocio Clave")

    pdf.subsection("6.1 NHM  - Numero de Historia Medica")
    pdf.body(
        "Identificador secuencial unico asignado automaticamente al crear "
        "un paciente. Se genera con SELECT MAX(nhm) + 1 protegido por "
        "pg_advisory_xact_lock(1001) para serializar accesos concurrentes "
        "y evitar duplicados. Complejidad: O(1) con el advisory lock."
    )
    pdf.code_block(
        '-- Generacion atomica del NHM\n'
        'SELECT pg_advisory_xact_lock(1001);\n'
        'SELECT COALESCE(MAX(nhm), 0) + 1 FROM patients WHERE status = \'A\';'
    )

    pdf.subsection("6.2 Campo is_new (primera vez)")
    pdf.body(
        "Flag booleano que indica si el paciente es primera vez. "
        "Impacta la duracion de las citas: 60 minutos para pacientes nuevos "
        "vs 30 minutos para recurrentes. Se usa en el calculo de slots "
        "disponibles del modulo de citas."
    )

    pdf.subsection("6.3 Relacion universitaria (university_relation)")
    pdf.body(
        "Campo obligatorio que clasifica al paciente segun su vinculo con "
        "la ULA. Valores esperados: estudiante, personal, docente, familia, "
        "externo. Se utiliza en el dashboard para metricas de distribucion "
        "y en el modulo de farmacia para limites de despacho."
    )

    pdf.subsection("6.4 Composicion de campos (portal register)")
    pdf.body(
        "El endpoint de registro del portal recibe campos atomicos que el "
        "backend compone en estructuras JSONB:"
    )
    pdf.bullet("country + state_geo + city -> birth_place (concatenacion)")
    pdf.bullet("blood_type + allergies + medical_alerts -> medical_data (JSONB)")
    pdf.bullet("emergency_name/relationship/phone/address -> emergency_contact (JSONB)")
    pdf.bullet("holder_cedula -> busqueda del titular -> fk_holder_patient_id")

    pdf.subsection("6.5 Soft Delete")
    pdf.body(
        "Los pacientes nunca se eliminan fisicamente. El mixin SoftDeleteMixin "
        "marca el registro con status='T' y registra deleted_at/deleted_by. "
        "Todas las consultas excluyen registros con status != 'A'."
    )

    # ================================================================
    # SECTION 7  - Auth
    # ================================================================
    pdf.subsection("7. Autenticacion y Autorizacion")
    pdf.add_table(
        ["Endpoint", "Auth", "Justificacion"],
        [
            ["GET /patients", "Opcional", "Portal publico puede buscar"],
            ["GET /patients/full", "Opcional", "Acceso a datos completos"],
            ["GET /patients/max-nhm", "Requerida", "Solo staff administrativo"],
            ["GET /patients/{id}", "Opcional", "Consulta por ID"],
            ["POST /patients", "Requerida", "Solo staff puede crear"],
            ["POST /patients/register", "Opcional", "Auto-registro portal ULA"],
            ["GET /patients/demographics", "Requerida", "Solo dashboard admin"],
        ],
        col_widths=[62, 30, 98],
    )
    pdf.ln(3)
    pdf.body(
        "Autenticacion 'Requerida' usa get_current_user_id (JWT obligatorio). "
        "'Opcional' usa get_optional_user_id (permite anonimo, retorna "
        "'anonymous' si no hay token)."
    )

    # ================================================================
    # Summary table  - last page
    # ================================================================
    pdf.add_page()
    pdf.section_title("Resumen de Endpoints")
    pdf.add_table(
        ["Metodo", "Ruta", "Auth", "Descripcion"],
        [
            ["GET", "/api/patients", "Opc.", "Listar / buscar (paginado)"],
            ["GET", "/api/patients/full", "Opc.", "Paciente completo por id|cedula|nhm"],
            ["GET", "/api/patients/max-nhm", "Req.", "Maximo NHM registrado"],
            ["GET", "/api/patients/{id}", "Opc.", "Paciente por UUID"],
            ["POST", "/api/patients", "Req.", "Crear paciente (NHM auto)"],
            ["POST", "/api/patients/register", "Opc.", "Registro portal ULA"],
            ["GET", "/api/patients/demographics", "Req.", "Estadisticas demograficas"],
            ["", "", "", ""],
            ["GET", "/api/medical-records/patient/{id}", "Opc.", "Historial medico"],
            ["GET", "/api/medical-records/orders/patient/{id}", "Opc.", "Ordenes de examenes"],
            ["GET", "/api/dashboard", "Req.", "KPIs consolidados (inc. pacientes)"],
        ],
        col_widths=[18, 72, 15, 85],
    )

    # Save
    pdf.output(str(OUTPUT))
    print(f"PDF generated: {OUTPUT}")
    print(f"Pages: {pdf.pages_count}")


if __name__ == "__main__":
    build()
