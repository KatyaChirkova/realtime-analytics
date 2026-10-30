from __future__ import annotations


def occupancy_percent(current_visitors: int, capacity: int) -> float:
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if current_visitors < 0:
        raise ValueError("current_visitors cannot be negative")
    return round(current_visitors / capacity * 100, 1)
