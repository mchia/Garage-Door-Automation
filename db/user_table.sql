CREATE TABLE
    IF NOT EXISTS users (
        id INTEGER NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        role TEXT,
        password TEXT NOT NULL,
        PRIMARY KEY ("id" AUTOINCREMENT)
    );