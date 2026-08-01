CREATE TABLE observations (
    run_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    contributor_key TEXT NOT NULL,
    receipt_sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    received_at TEXT NOT NULL,
    withdrawn_at TEXT
);

CREATE INDEX observations_status_received
ON observations(status, received_at);

CREATE INDEX observations_contributor_received
ON observations(contributor_key, received_at);
