"""Seeder de schemas de formularios médicos para CAMIULA.

Siembra un schema base por cada especialidad activa en el sistema.
Cada schema define las secciones y campos del formulario médico dinámico
que el frontend renderiza durante una consulta.

Idempotente: no reemplaza schemas que ya existan (upsert por id).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.form_schemas.infrastructure.models import FormSchemaModel
from app.shared.database.seeder import BaseSeeder

# ---------------------------------------------------------------------------
# Definición de schemas por especialidad
# ---------------------------------------------------------------------------

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

FORM_SCHEMAS = [
    {
        "id": "medicina-general-v1",
        "version": "1.0",
        "specialtyId": "medicina-general",
        "specialtyName": "Medicina General",
        "sections": [
            {
                "id": "motivo",
                "title": "Motivo de Consulta",
                "groups": [
                    {
                        "id": "motivo-group",
                        "fields": [
                            {
                                "key": "motivo_consulta",
                                "type": "textarea",
                                "label": "Motivo de consulta",
                                "placeholder": "Describa el motivo de la consulta",
                                "validation": {"required": True, "maxLength": 500},
                            }
                        ],
                    }
                ],
            },
            {
                "id": "signos-vitales",
                "title": "Signos Vitales",
                "groups": [
                    {
                        "id": "sv-group",
                        "fields": [
                            {
                                "key": "presion_arterial",
                                "type": "text",
                                "label": "Presión arterial (mmHg)",
                                "placeholder": "120/80",
                                "validation": {"required": False},
                            },
                            {
                                "key": "frecuencia_cardiaca",
                                "type": "number",
                                "label": "Frecuencia cardíaca (lpm)",
                                "validation": {"required": False, "min": 30, "max": 250},
                            },
                            {
                                "key": "temperatura",
                                "type": "number",
                                "label": "Temperatura (°C)",
                                "validation": {"required": False, "min": 34, "max": 42},
                            },
                            {
                                "key": "frecuencia_respiratoria",
                                "type": "number",
                                "label": "Frecuencia respiratoria (rpm)",
                                "validation": {"required": False},
                            },
                            {
                                "key": "peso_kg",
                                "type": "number",
                                "label": "Peso (kg)",
                                "validation": {"required": False},
                            },
                            {
                                "key": "talla_cm",
                                "type": "number",
                                "label": "Talla (cm)",
                                "validation": {"required": False},
                            },
                        ],
                    }
                ],
            },
            {
                "id": "evaluacion",
                "title": "Evaluación Clínica",
                "groups": [
                    {
                        "id": "eval-group",
                        "fields": [
                            {
                                "key": "anamnesis",
                                "type": "textarea",
                                "label": "Anamnesis",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                            {
                                "key": "examen_fisico",
                                "type": "textarea",
                                "label": "Examen físico",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                            {
                                "key": "diagnostico",
                                "type": "textarea",
                                "label": "Diagnóstico",
                                "validation": {"required": True, "maxLength": 500},
                            },
                            {
                                "key": "tratamiento",
                                "type": "textarea",
                                "label": "Tratamiento / Plan",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": "odontologia-v1",
        "version": "1.0",
        "specialtyId": "odontologia",
        "specialtyName": "Odontología",
        "sections": [
            {
                "id": "motivo",
                "title": "Motivo de Consulta",
                "groups": [
                    {
                        "id": "motivo-group",
                        "fields": [
                            {
                                "key": "motivo_consulta",
                                "type": "textarea",
                                "label": "Motivo de consulta",
                                "validation": {"required": True, "maxLength": 500},
                            }
                        ],
                    }
                ],
            },
            {
                "id": "odontograma",
                "title": "Evaluación Dental",
                "groups": [
                    {
                        "id": "dental-group",
                        "fields": [
                            {
                                "key": "piezas_afectadas",
                                "type": "text",
                                "label": "Piezas dentales afectadas",
                                "placeholder": "Ej: 16, 21, 36",
                                "validation": {"required": False},
                            },
                            {
                                "key": "tipo_lesion",
                                "type": "select",
                                "label": "Tipo de lesión",
                                "options": [
                                    {"value": "caries", "label": "Caries"},
                                    {"value": "fractura", "label": "Fractura"},
                                    {"value": "periodontitis", "label": "Periodontitis"},
                                    {"value": "pulpitis", "label": "Pulpitis"},
                                    {"value": "otro", "label": "Otro"},
                                ],
                                "validation": {"required": False},
                            },
                            {
                                "key": "higiene_oral",
                                "type": "select",
                                "label": "Higiene oral",
                                "options": [
                                    {"value": "buena", "label": "Buena"},
                                    {"value": "regular", "label": "Regular"},
                                    {"value": "deficiente", "label": "Deficiente"},
                                ],
                                "validation": {"required": False},
                            },
                            {
                                "key": "procedimiento",
                                "type": "textarea",
                                "label": "Procedimiento realizado",
                                "validation": {"required": True, "maxLength": 500},
                            },
                            {
                                "key": "indicaciones",
                                "type": "textarea",
                                "label": "Indicaciones post-procedimiento",
                                "validation": {"required": False, "maxLength": 500},
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": "psicologia-v1",
        "version": "1.0",
        "specialtyId": "psicologia",
        "specialtyName": "Psicología",
        "sections": [
            {
                "id": "motivo",
                "title": "Motivo de Consulta",
                "groups": [
                    {
                        "id": "motivo-group",
                        "fields": [
                            {
                                "key": "motivo_consulta",
                                "type": "textarea",
                                "label": "Motivo de consulta",
                                "validation": {"required": True, "maxLength": 500},
                            },
                            {
                                "key": "tipo_consulta",
                                "type": "select",
                                "label": "Tipo de consulta",
                                "options": [
                                    {"value": "primera_vez", "label": "Primera vez"},
                                    {"value": "seguimiento", "label": "Seguimiento"},
                                    {"value": "crisis", "label": "Crisis / Urgencia"},
                                ],
                                "validation": {"required": True},
                            },
                        ],
                    }
                ],
            },
            {
                "id": "evaluacion",
                "title": "Evaluación Psicológica",
                "groups": [
                    {
                        "id": "eval-group",
                        "fields": [
                            {
                                "key": "estado_mental",
                                "type": "textarea",
                                "label": "Examen del estado mental",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                            {
                                "key": "antecedentes",
                                "type": "textarea",
                                "label": "Antecedentes psicológicos / psiquiátricos",
                                "validation": {"required": False, "maxLength": 500},
                            },
                            {
                                "key": "factores_estres",
                                "type": "textarea",
                                "label": "Factores estresores identificados",
                                "validation": {"required": False, "maxLength": 500},
                            },
                            {
                                "key": "impresion_diagnostica",
                                "type": "textarea",
                                "label": "Impresión diagnóstica",
                                "validation": {"required": True, "maxLength": 500},
                            },
                            {
                                "key": "plan_intervencion",
                                "type": "textarea",
                                "label": "Plan de intervención",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                            {
                                "key": "proxima_sesion",
                                "type": "text",
                                "label": "Próxima sesión sugerida",
                                "placeholder": "Ej: 2 semanas",
                                "validation": {"required": False},
                            },
                        ],
                    }
                ],
            },
        ],
    },
    {
        "id": "nutricion-v1",
        "version": "1.0",
        "specialtyId": "nutricion",
        "specialtyName": "Nutrición",
        "sections": [
            {
                "id": "motivo",
                "title": "Motivo de Consulta",
                "groups": [
                    {
                        "id": "motivo-group",
                        "fields": [
                            {
                                "key": "motivo_consulta",
                                "type": "textarea",
                                "label": "Motivo de consulta",
                                "validation": {"required": True, "maxLength": 500},
                            }
                        ],
                    }
                ],
            },
            {
                "id": "antropometria",
                "title": "Datos Antropométricos",
                "groups": [
                    {
                        "id": "antro-group",
                        "fields": [
                            {
                                "key": "peso_kg",
                                "type": "number",
                                "label": "Peso (kg)",
                                "validation": {"required": True},
                            },
                            {
                                "key": "talla_cm",
                                "type": "number",
                                "label": "Talla (cm)",
                                "validation": {"required": True},
                            },
                            {
                                "key": "imc",
                                "type": "number",
                                "label": "IMC (calculado)",
                                "validation": {"required": False},
                            },
                            {
                                "key": "circunferencia_abdominal",
                                "type": "number",
                                "label": "Circunferencia abdominal (cm)",
                                "validation": {"required": False},
                            },
                        ],
                    }
                ],
            },
            {
                "id": "habitos",
                "title": "Hábitos Alimentarios",
                "groups": [
                    {
                        "id": "habitos-group",
                        "fields": [
                            {
                                "key": "frecuencia_comidas",
                                "type": "select",
                                "label": "Comidas por día",
                                "options": [
                                    {"value": "1-2", "label": "1-2 veces"},
                                    {"value": "3", "label": "3 veces"},
                                    {"value": "4-5", "label": "4-5 veces"},
                                ],
                                "validation": {"required": False},
                            },
                            {
                                "key": "consume_agua",
                                "type": "number",
                                "label": "Consumo de agua diario (litros)",
                                "validation": {"required": False},
                            },
                            {
                                "key": "actividad_fisica",
                                "type": "select",
                                "label": "Nivel de actividad física",
                                "options": [
                                    {"value": "sedentario", "label": "Sedentario"},
                                    {"value": "leve", "label": "Leve (1-2 días/semana)"},
                                    {"value": "moderado", "label": "Moderado (3-4 días/semana)"},
                                    {"value": "intenso", "label": "Intenso (5+ días/semana)"},
                                ],
                                "validation": {"required": False},
                            },
                            {
                                "key": "plan_nutricional",
                                "type": "textarea",
                                "label": "Plan nutricional indicado",
                                "validation": {"required": False, "maxLength": 1000},
                            },
                        ],
                    }
                ],
            },
        ],
    },
]

# IDs de los schemas para el método clear()
SCHEMA_IDS = [s["id"] for s in FORM_SCHEMAS]


class FormSchemaSeeder(BaseSeeder):
    """Siembra schemas de formularios médicos para CAMIULA.

    Idempotente: omite schemas que ya existen (por id).
    order=50 — depende de que las especialidades ya estén sembradas (order=15).
    """

    order = 50

    async def run(self, session: AsyncSession) -> None:
        for schema_data in FORM_SCHEMAS:
            existing = await session.execute(
                select(FormSchemaModel).where(
                    FormSchemaModel.id == schema_data["id"]
                )
            )
            if existing.scalar_one_or_none():
                continue

            session.add(
                FormSchemaModel(
                    id=schema_data["id"],
                    version=schema_data["version"],
                    specialty_id=schema_data["specialtyId"],
                    specialty_name=schema_data["specialtyName"],
                    schema_json=schema_data,
                    created_by=SYSTEM_USER_ID,
                )
            )

    async def clear(self, session: AsyncSession) -> None:
        from sqlalchemy import delete

        await session.execute(
            delete(FormSchemaModel).where(
                FormSchemaModel.id.in_(SCHEMA_IDS)
            )
        )
