from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class Role:
    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    description: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
