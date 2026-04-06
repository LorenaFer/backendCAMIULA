"""DTOs del caso de uso de Medicamentos."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateMedicationDTO:
    code: str
    generic_name: str
    pharmaceutical_form: str
    unit_measure: str
    controlled_substance: bool
    requires_refrigeration: bool
    commercial_name: Optional[str] = None
    concentration: Optional[str] = None
    therapeutic_class: Optional[str] = None
    fk_category_id: Optional[str] = None


@dataclass
class UpdateMedicationDTO:
    generic_name: Optional[str] = None
    commercial_name: Optional[str] = None
    pharmaceutical_form: Optional[str] = None
    concentration: Optional[str] = None
    unit_measure: Optional[str] = None
    therapeutic_class: Optional[str] = None
    fk_category_id: Optional[str] = None
    controlled_substance: Optional[bool] = None
    requires_refrigeration: Optional[bool] = None
    medication_status: Optional[str] = None
