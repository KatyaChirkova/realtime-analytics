CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    student_code VARCHAR(32) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS visit_events (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id),
    event_type VARCHAR(5) NOT NULL CHECK (event_type IN ('ENTER', 'EXIT')),
    event_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visit_events_time
    ON visit_events(event_time DESC);

CREATE INDEX IF NOT EXISTS idx_visit_events_student_time
    ON visit_events(student_id, event_time DESC);
