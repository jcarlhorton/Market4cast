-- Market4cast Database Schema
-- Optimized for SQLite with Write-Ahead Logging (WAL) mode

-- Table for tracking currently active predictions
CREATE TABLE IF NOT EXISTS active_predictions (
    ticker TEXT PRIMARY KEY,
    announcement_date TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    entry_price REAL NOT NULL,
    predicted_target_price REAL NOT NULL,
    predicted_target_pct REAL NOT NULL,
    stop_loss_price REAL NOT NULL,
    suggested_position_size REAL, -- % of portfolio
    sector TEXT,
    catalyst_summary TEXT,
    llm_guidance_score REAL,
    days_active INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE' -- ACTIVE, CLOSED, CANCELLED
);

-- Table for historical prediction outcomes and performance tracking
CREATE TABLE IF NOT EXISTS historical_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    announcement_date TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    exit_date TEXT NOT NULL,
    predicted_target_pct REAL NOT NULL,
    actual_return_pct REAL NOT NULL,
    success BOOLEAN, -- actual_return_pct >= predicted_target_pct
    max_favorable_excursion REAL, -- highest % gain during period
    max_adverse_excursion REAL, -- lowest % loss during period
    exit_reason TEXT -- TARGET_HIT, STOP_LOSS, TIME_EXIT (60 days)
);

-- Table for system-wide health and risk metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_name TEXT PRIMARY KEY,
    metric_value REAL NOT NULL,
    last_updated TEXT NOT NULL
);

-- Initialize default system metrics
INSERT OR IGNORE INTO system_metrics (metric_name, metric_value, last_updated) VALUES ('system_confidence_score', 0.0, datetime('now'));
INSERT OR IGNORE INTO system_metrics (metric_name, metric_value, last_updated) VALUES ('total_predictions_closed', 0.0, datetime('now'));
INSERT OR IGNORE INTO system_metrics (metric_name, metric_value, last_updated) VALUES ('rolling_mae', 0.0, datetime('now'));
