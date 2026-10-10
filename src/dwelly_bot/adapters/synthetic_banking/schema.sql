-- Only decision-time evidence belongs here. No labels, outcomes or final entity state.
PRAGMA foreign_keys = ON;
CREATE TABLE snapshots (scope_id TEXT PRIMARY KEY, as_of TEXT NOT NULL, bank_id TEXT NOT NULL);
CREATE TABLE banks (bank_id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE systems (system_id TEXT PRIMARY KEY, description TEXT NOT NULL);
CREATE TABLE contacts (
    scope_id TEXT NOT NULL REFERENCES snapshots(scope_id),
    contact_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    PRIMARY KEY (scope_id, contact_id)
);
CREATE TABLE messages (
    scope_id TEXT NOT NULL REFERENCES snapshots(scope_id), seq INTEGER NOT NULL,
    at TEXT NOT NULL, channel TEXT NOT NULL, sender TEXT NOT NULL, recipient TEXT NOT NULL,
    body TEXT NOT NULL, authenticated INTEGER, actor_kind TEXT NOT NULL,
    PRIMARY KEY (scope_id, seq)
);
CREATE TABLE responses (
    scope_id TEXT NOT NULL REFERENCES snapshots(scope_id), system_id TEXT NOT NULL,
    query_hint TEXT NOT NULL, response_text TEXT NOT NULL,
    fields_available TEXT NOT NULL, fields_absent TEXT NOT NULL,
    PRIMARY KEY (scope_id, system_id, query_hint)
);
CREATE TABLE documents (
    scope_id TEXT NOT NULL REFERENCES snapshots(scope_id), filename TEXT NOT NULL,
    available_at TEXT NOT NULL, media_type TEXT NOT NULL, sha256 TEXT NOT NULL,
    text TEXT, extraction_status TEXT NOT NULL,
    PRIMARY KEY (scope_id, filename)
);
