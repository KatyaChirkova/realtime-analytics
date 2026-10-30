from __future__ import annotations

import argparse
import math
import random
from datetime import datetime, timedelta, timezone

from database import init_db, insert_event


def activity_multiplier(hour: float) -> float:
    """Smooth daily pattern: low morning/evening, peak around 13:00-15:00."""
    peak = math.exp(-((hour - 13.5) ** 2) / (2 * 2.2**2))
    secondary = 0.25 * math.exp(-((hour - 10.0) ** 2) / (2 * 1.3**2))
    return min(1.0, 0.18 + 0.72 * peak + secondary)


def seed(hours: int, count: int, seed_value: int = 42) -> None:
    rng = random.Random(seed_value)
    students = [f"student_{i:03d}" for i in range(1, count + 1)]
    now = datetime.now(timezone.utc)
    inside: set[str] = set()
    events = []

    start = now - timedelta(hours=hours)
    for minute in range(hours * 60):
        current = start + timedelta(minutes=minute)
        hour = current.hour + current.minute / 60
        target_count = int(count * activity_multiplier(hour))

        delta = target_count - len(inside)
        if delta > 0:
            # Spread entries over the minute instead of generating huge spikes.
            amount = min(delta, rng.randint(0, 2))
            for _ in range(amount):
                candidates = [s for s in students if s not in inside]
                if not candidates:
                    break
                student = rng.choice(candidates)
                inside.add(student)
                events.append((student, "ENTER", current))
        elif delta < 0:
            amount = min(-delta, rng.randint(0, 2))
            for _ in range(amount):
                if not inside:
                    break
                student = rng.choice(list(inside))
                inside.remove(student)
                events.append((student, "EXIT", current))

    for student, event_type, event_time in events:
        insert_event(student, event_type, event_time)

    print(f"Создано исторических событий: {len(events)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Заполнение БД историей")
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--students", type=int, default=80)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    init_db(reset=args.reset)
    seed(args.hours, args.students)
