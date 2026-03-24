from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class Permission:
    code: str
    module: str
    id: str = field(default_factory=lambda: str(uuid4()))
    description: Optional[str] = None
