-- 001_initial.sql
-- Forward-only migration establishing the initial schema.

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    description TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS smb_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_path TEXT NOT NULL,
    output_path TEXT NOT NULL,
    share_url TEXT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO smb_config (id, input_path, output_path, share_url, username, password)
VALUES (1, '/input', '/output', 'smb://localhost/videos', 'demo', 'demo');

CREATE TABLE IF NOT EXISTS encoding_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    tool TEXT NOT NULL,
    video_codec TEXT NOT NULL,
    audio_codec TEXT NOT NULL,
    quality_target TEXT NOT NULL,
    preset TEXT,
    container TEXT,
    inherits_profile_id INTEGER REFERENCES encoding_profiles(id),
    is_high_quality INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO encoding_profiles (id, name, tool, video_codec, audio_codec, quality_target, preset, container, inherits_profile_id, is_high_quality)
VALUES
    (1, 'default', 'handbrake', 'H.265', 'aac', 'crf23', NULL, 'mp4', NULL, 0),
    (2, 'high_quality', 'handbrake', 'H.265', 'aac', 'crf20', NULL, 'mp4', 1, 1);

CREATE TABLE IF NOT EXISTS encoding_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    min_size_mb REAL,
    max_size_mb REAL,
    min_duration_seconds INTEGER,
    max_duration_seconds INTEGER,
    min_resolution_height INTEGER,
    max_resolution_height INTEGER,
    profile_id INTEGER NOT NULL REFERENCES encoding_profiles(id),
    high_quality_only INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO encoding_rules (
    id,
    name,
    min_size_mb,
    max_size_mb,
    min_duration_seconds,
    max_duration_seconds,
    min_resolution_height,
    max_resolution_height,
    profile_id,
    high_quality_only
)
VALUES
    (1, 'default-small', 0, 500, NULL, 7200, NULL, 1080, 1, 0),
    (2, 'default-large-high-quality', 500, NULL, NULL, NULL, NULL, NULL, 2, 1);

CREATE TABLE IF NOT EXISTS queue_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_name TEXT NOT NULL UNIQUE,
    source_path TEXT NOT NULL,
    manifest_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    stage TEXT NOT NULL DEFAULT 'pending',
    progress REAL NOT NULL DEFAULT 0,
    requested_profile TEXT,
    actual_profile_id INTEGER REFERENCES encoding_profiles(id),
    high_quality INTEGER NOT NULL DEFAULT 0,
    file_size_mb REAL,
    duration_seconds INTEGER,
    resolution_height INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS job_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES queue_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_initial');

COMMIT;
