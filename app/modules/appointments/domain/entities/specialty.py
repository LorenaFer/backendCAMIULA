from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Specialty:
    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
