CREATE TABLE IF NOT EXISTS logbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    ip_address TEXT,
    login_date TEXT,
    login_time TEXT,
    browser TEXT,
    browser_version TEXT,
    os TEXT,
    os_version TEXT,
    device TEXT
);