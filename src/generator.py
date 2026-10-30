from __future__ import annotations

import argparse
import random
import time
from datetime import datetime, timezone

from database import init_db, insert_event

STUDENTS = [f"student_{i:03d}" for i in range(1, 81)]


def get_current_inside() -> set[str]:
    query = """
        SELECT s.student_code
        FROM (
            SELECT DISTINCT ON (student_id)
                student_id, event_type, event_time, id
            FROM visit_events
            ORDER BY student_id, event_time DESC, id DESC
        ) latest
        JOIN students s ON s.id = latest.student_id
        WHERE latest.event_type = 'ENTER'
    """
    from database import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return {row["student_code"] for row in cur.fetchall()}


def run(interval: float, duration: int | None, seed: int | None = 42) -> None:
    rng = random.Random(seed)
    inside: set[str] = get_current_inside()
    started = time.monotonic()

    while duration is None or time.monotonic() - started < duration:
        # Небольшая модель поведения библиотеки: утром чаще входы,
        # вечером чаще выходы. В прототипе это всё равно генерация событий.
        hour = datetime.now().hour
        if 9 <= hour < 15:
            enter_probability = 0.68
        elif 15 <= hour < 18:
            enter_probability = 0.45
        else:
            enter_probability = 0.25

        available = [s for s in STUDENTS if s not in inside]
        leaving = list(inside)

        if not inside:
            event_type = "ENTER"
        elif not available:
            event_type = "EXIT"
        else:
            event_type = "ENTER" if rng.random() < enter_probability else "EXIT"

        if event_type == "ENTER":
            student = rng.choice(available)
            inside.add(student)
        else:
            student = rng.choice(leaving)
            inside.remove(student)

        event_time = datetime.now(timezone.utc)
        event_id = insert_event(student, event_type, event_time)
        print(f"event_id={event_id} {event_time.isoformat()} {event_type} {student}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генератор событий библиотеки")
    parser.add_argument("--interval", type=float, default=20.0)
    parser.add_argument("--duration", type=int, default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset:
        init_db(reset=True)
    else:
        init_db()

    run(args.interval, args.duration)
