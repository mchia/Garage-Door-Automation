CREATE TABLE IF NOT EXISTS ip_logs (
    ip_address TEXT PRIMARY KEY,
    city TEXT,
    region TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL
);