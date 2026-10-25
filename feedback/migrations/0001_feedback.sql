CREATE TABLE IF NOT EXISTS feedback (
    artwork_id TEXT NOT NULL,
    viewer_hash TEXT NOT NULL,
    beauty INTEGER CHECK (beauty IS NULL OR beauty BETWEEN 1 AND 5),
    inspiration INTEGER CHECK (inspiration IS NULL OR inspiration BETWEEN 1 AND 5),
    feelings TEXT NOT NULL DEFAULT '[]',
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (artwork_id, viewer_hash)
);
CREATE INDEX IF NOT EXISTS feedback_updated ON feedback(updated_at);
