"""Pydantic schemas for the Dashboard BI module."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class KpisResponse(BaseModel):
    total_appointments: int = 0
    appointments_today: int = 0
    pending_appointments: int = 0
    attendance_rate: float = 0.0
    no_show_rate: float = 0.0
    cancellation_rate: float = 0.0
    total_patients: int = 0
    new_patients: int = 0
    total_doctors: int = 0
    inventory_value: float = 0.0


class SpecialtyCount(BaseModel):
    name: str
    count: int


class HourlyItem(BaseModel):
    hour: str
    count: int


class OccupancyItem(BaseModel):
    name: str
    available_slots: int
    booked: int


class AbsenteeismItem(BaseModel):
    name: str
    total: int
    no_shows: int
    rate: float


class PerformanceItem(BaseModel):
    name: str
    specialty: str
    count: int
    attended: int


class DiagnosisItem(BaseModel):
    code: str
    description: str
    count: int


class InventorySummary(BaseModel):
    total_medications: int = 0
    critical_stock: int = 0
    expiring_batches: int = 0
    estimated_value: float = 0.0


class ConsumptionItem(BaseModel):
    medication_id: str
    generic_name: str
    total_dispatched: int
    patient_count: int


class DashboardResponse(BaseModel):
    date_str: str
    generated_at: str
    kpis: KpisResponse
    appointments_by_status: Dict[str, int]
    appointments_by_specialty: List[SpecialtyCount]
    daily_trend: List[int]
    hourly_distribution: List[HourlyItem]
    heatmap: List[List[int]]
    occupancy_by_specialty: List[OccupancyItem]
    absenteeism_by_specialty: List[AbsenteeismItem]
    performance_by_doctor: List[PerformanceItem]
    patients_by_type: Dict[str, int]
    patients_by_sex: Dict[str, int]
    first_time_count: int
    returning_count: int
    top_diagnoses: List[DiagnosisItem]
    inventory: InventorySummary
    top_consumption: List[ConsumptionItem]


class DemographicsResponse(BaseModel):
    patients_by_type: Dict[str, int]
    patients_by_sex: Dict[str, int]
    first_time_count: int
    returning_count: int


class HeatmapResponse(BaseModel):
    date_from: str
    date_to: str
    heatmap: List[List[int]]


class AvailabilitySummaryItem(BaseModel):
    specialty: str
    total_doctors: int
    total_blocks: int


class TopDiagnosisResponse(BaseModel):
    items: List[DiagnosisItem]
