from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from database import get_connection
from metrics import occupancy_percent


def get_current_visitors() -> int:
    query = """
        SELECT COUNT(*) AS current_visitors
        FROM (
            SELECT DISTINCT ON (student_id)
                student_id, event_type, event_time, id
            FROM visit_events
            ORDER BY student_id, event_time DESC, id DESC
        ) latest
        WHERE event_type = 'ENTER'
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return int(cur.fetchone()["current_visitors"])


def get_occupancy_percent(capacity: int) -> float:
    return occupancy_percent(get_current_visitors(), capacity)


def _full_hour_index(hours: int) -> pd.DatetimeIndex:
    now = datetime.now(timezone.utc)
    end_hour = pd.Timestamp(now).floor("h")
    return pd.date_range(end=end_hour, periods=hours, freq="h", tz="UTC")


def get_hourly_history(hours: int = 24) -> pd.DataFrame:
    """Return hourly entry/exit counts with a complete time axis."""
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = """
        SELECT
            date_trunc('hour', event_time) AS hour,
            COUNT(*) FILTER (WHERE event_type = 'ENTER')::int AS entries,
            COUNT(*) FILTER (WHERE event_type = 'EXIT')::int AS exits
        FROM visit_events
        WHERE event_time >= %s
        GROUP BY 1
        ORDER BY 1
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (start,))
            rows = cur.fetchall()

    index = _full_hour_index(hours)
    df = pd.DataFrame(rows, columns=["hour", "entries", "exits"])

    if df.empty:
        return pd.DataFrame(
            {
                "hour": index,
                "entries": [0] * len(index),
                "exits": [0] * len(index),
            }
        )

    df["hour"] = pd.to_datetime(df["hour"], utc=True)
    df = df.set_index("hour").reindex(index, fill_value=0).rename_axis("hour").reset_index()
    df["entries"] = df["entries"].astype(int)
    df["exits"] = df["exits"].astype(int)
    return df


def get_occupancy_history(hours: int = 24) -> pd.DataFrame:
    """Return estimated library occupancy at the end of each hour."""
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    index = _full_hour_index(hours)

    # State at the beginning of the requested window: last event for each
    # student strictly before the window start.
    start_state_query = """
        SELECT COUNT(*) AS visitors_at_start
        FROM (
            SELECT DISTINCT ON (student_id)
                student_id, event_type, event_time, id
            FROM visit_events
            WHERE event_time < %s
            ORDER BY student_id, event_time DESC, id DESC
        ) latest
        WHERE event_type = 'ENTER'
    """

    hourly_query = """
        SELECT
            date_trunc('hour', event_time) AS hour,
            COUNT(*) FILTER (WHERE event_type = 'ENTER')::int AS entries,
            COUNT(*) FILTER (WHERE event_type = 'EXIT')::int AS exits
        FROM visit_events
        WHERE event_time >= %s
        GROUP BY 1
        ORDER BY 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(start_state_query, (start,))
            visitors = int(cur.fetchone()["visitors_at_start"])
            cur.execute(hourly_query, (start,))
            rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=["hour", "entries", "exits"])
    if df.empty:
        return pd.DataFrame({"hour": index, "occupancy": [visitors] * len(index)})

    df["hour"] = pd.to_datetime(df["hour"], utc=True)
    df = df.set_index("hour").reindex(index, fill_value=0).rename_axis("hour").reset_index()
    df["entries"] = df["entries"].astype(int)
    df["exits"] = df["exits"].astype(int)

    # Build the occupancy curve hour by hour, keeping values non-negative.
    levels = []
    current = visitors
    for _, row in df.iterrows():
        current = max(current + int(row["entries"]) - int(row["exits"]), 0)
        levels.append(current)

    result = df[["hour"]].copy()
    result["occupancy"] = levels
    return result


def get_recent_events(limit: int = 12) -> pd.DataFrame:
    query = """
        SELECT
            e.id,
            s.student_code,
            e.event_type,
            e.event_time
        FROM visit_events e
        JOIN students s ON s.id = e.student_id
        ORDER BY e.event_time DESC, e.id DESC
        LIMIT %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["id", "student_code", "event_type", "event_time"])


def get_peak_hour(hours: int = 24) -> tuple[str, int]:
    query = """
        SELECT
            EXTRACT(HOUR FROM event_time)::int AS hour,
            COUNT(*) FILTER (WHERE event_type = 'ENTER')::int AS entries
        FROM visit_events
        WHERE event_time >= NOW() - make_interval(hours => %s)
        GROUP BY 1
        ORDER BY entries DESC, hour
        LIMIT 1
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (hours,))
            row = cur.fetchone()
            if not row:
                return "—", 0
            return f"{row['hour']:02d}:00", int(row["entries"])
