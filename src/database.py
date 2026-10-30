from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from config import settings

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(settings.dsn, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(reset: bool = False) -> None:
    schema = (SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cur:
            if reset:
                cur.execute("DROP TABLE IF EXISTS visit_events CASCADE")
                cur.execute("DROP TABLE IF EXISTS students CASCADE")
            cur.execute(schema)


def ensure_student(student_code: str) -> int:
    query = """
        INSERT INTO students(student_code)
        VALUES (%s)
        ON CONFLICT (student_code)
        DO UPDATE SET student_code = EXCLUDED.student_code
        RETURNING id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_code,))
            return int(cur.fetchone()["id"])


def insert_event(student_code: str, event_type: str, event_time) -> int:
    if event_type not in {"ENTER", "EXIT"}:
        raise ValueError("event_type must be ENTER or EXIT")

    query = """
        INSERT INTO visit_events(student_id, event_type, event_time)
        VALUES (
            (SELECT id FROM students WHERE student_code = %s),
            %s,
            %s
        )
        RETURNING id
    """
    ensure_student(student_code)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_code, event_type, event_time))
            return int(cur.fetchone()["id"])
