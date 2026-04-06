"""DTOs for Specialty use cases."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateSpecialtyDTO:
    name: str


@dataclass
class UpdateSpecialtyDTO:
    name: Optional[str] = None
