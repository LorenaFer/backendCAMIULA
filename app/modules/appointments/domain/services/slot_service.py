"""Lógica pura de dominio para cálculo de slots y detección de conflictos.

No depende de BD ni frameworks — puro Python.
"""

from datetime import time, timedelta, datetime


def time_to_minutes(t: time) -> int:
    """Convierte time a minutos desde medianoche."""
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """Convierte minutos desde medianoche a time."""
    return time(minutes // 60, minutes % 60)


def generate_slots(start_time: time, end_time: time, duration: int) -> list[dict]:
    """Genera slots disponibles entre start y end con duración dada.

    Returns: [{"start": time, "end": time}, ...]
    """
    slots = []
    start_min = time_to_minutes(start_time)
    end_min = time_to_minutes(end_time)

    current = start_min
    while current + duration <= end_min:
        slot_start = minutes_to_time(current)
        slot_end = minutes_to_time(current + duration)
        slots.append({"start": slot_start, "end": slot_end})
        current += duration

    return slots


def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    """Verifica si dos rangos de tiempo se solapan."""
    return start1 < end2 and start2 < end1
