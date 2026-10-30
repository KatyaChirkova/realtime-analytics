-- Текущее количество посетителей: число входов минус число выходов.
SELECT
    COUNT(*) FILTER (WHERE event_type = 'ENTER')
    - COUNT(*) FILTER (WHERE event_type = 'EXIT') AS current_visitors
FROM visit_events;

-- Текущее состояние каждого студента определяется последним событием.
WITH latest_events AS (
    SELECT DISTINCT ON (student_id)
        student_id,
        event_type,
        event_time
    FROM visit_events
    ORDER BY student_id, event_time DESC, id DESC
)
SELECT COUNT(*) AS current_visitors
FROM latest_events
WHERE event_type = 'ENTER';

-- Количество входов и выходов по часу.
SELECT
    date_trunc('hour', event_time) AS hour,
    COUNT(*) FILTER (WHERE event_type = 'ENTER') AS entries,
    COUNT(*) FILTER (WHERE event_type = 'EXIT') AS exits
FROM visit_events
WHERE event_time >= NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;
