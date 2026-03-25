"""Utilidades compartidas de la capa de presentación del módulo appointments."""

from datetime import time


def parse_time(s: str) -> time:
    """Parsea string HH:MM a time. Usado en request bodies de disponibilidad y citas."""
    parts = s.split(":")
    return time(int(parts[0]), int(parts[1]))
