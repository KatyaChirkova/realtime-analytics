from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from metrics import occupancy_percent  # noqa: E402


def test_occupancy_percent() -> None:
    assert occupancy_percent(60, 120) == 50.0
    assert occupancy_percent(0, 120) == 0.0


def test_invalid_capacity() -> None:
    try:
        occupancy_percent(10, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("capacity <= 0 must raise ValueError")


def test_invalid_visitor_count() -> None:
    try:
        occupancy_percent(-1, 120)
    except ValueError:
        pass
    else:
        raise AssertionError("negative visitors must raise ValueError")
