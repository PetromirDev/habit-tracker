CREATE TABLE periodicity (
    code TEXT PRIMARY KEY
);

INSERT INTO periodicity (code) VALUES
    ('daily'),
    ('weekly');

CREATE TABLE habit (
    id               INTEGER PRIMARY KEY,
    name             TEXT    NOT NULL COLLATE NOCASE UNIQUE CHECK (trim(name) <> ''),
    task             TEXT    NOT NULL CHECK (trim(task) <> ''),
    periodicity_code TEXT    NOT NULL REFERENCES periodicity (code),
    created_at       TEXT    NOT NULL CHECK (created_at = datetime(created_at))
);

CREATE TABLE completion (
    id           INTEGER PRIMARY KEY,
    habit_id     INTEGER NOT NULL REFERENCES habit (id) ON DELETE CASCADE,
    completed_at TEXT    NOT NULL CHECK (completed_at = datetime(completed_at))
);

CREATE INDEX idx_completion_habit_id_completed_at ON completion (habit_id, completed_at);

PRAGMA user_version = 1;
