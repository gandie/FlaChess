BEGIN;

WITH generated_names (name) AS (
    SELECT first_name || ' ' || last_name
    FROM unnest(ARRAY[
        'Aisha',
        'Arjun',
        'Clara',
        'Diego',
        'Elena',
        'Hugo',
        'Iris',
        'Jules',
        'Kofi',
        'Leila',
        'Marta',
        'Nora'
    ]) AS first_name
    CROSS JOIN unnest(ARRAY[
        'Andersen',
        'Bennett',
        'Costa',
        'Dubois',
        'Eriksen',
        'Fischer',
        'Gupta',
        'Hansen',
        'Ivanov',
        'Jensen',
        'Kowalski',
        'Moreau'
    ]) AS last_name
    ORDER BY random()
    LIMIT 24
)
INSERT INTO player (name)
SELECT name
FROM generated_names;

WITH generated_tournaments (name) AS (
    SELECT adjective || ' ' || event_name
    FROM unnest(ARRAY[
        'Autumn',
        'City',
        'Harbor',
        'Midnight',
        'North Star',
        'Riverside',
        'Spring',
        'Winter'
    ]) AS adjective
    CROSS JOIN unnest(ARRAY[
        'Blitz',
        'Chess Cup',
        'Classic',
        'Open',
        'Rapid',
        'Invitational'
    ]) AS event_name
    ORDER BY random()
    LIMIT 3
)
INSERT INTO tournament (name, description, lifecycle, time_control)
SELECT
    name,
    'Randomly seeded local development tournament.',
    'draft',
    '10+5'
FROM generated_tournaments;

COMMIT;
