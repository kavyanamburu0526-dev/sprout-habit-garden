import sqlite3
import os

DATABASE = os.path.join("instance", "sprout.db")


def get_db():
    os.makedirs("instance", exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '🌱',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_on TEXT NOT NULL,

            FOREIGN KEY(habit_id)
            REFERENCES habits(id)
            ON DELETE CASCADE,

            UNIQUE(habit_id, completed_on)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY,
            seeds INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL,
            cost INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER NOT NULL,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(plant_id)
            REFERENCES plants(id)
        )
    """)

    conn.execute("""
        INSERT OR IGNORE INTO app_state (id, seeds)
        VALUES (1, 0)
    """)

    plant_count = conn.execute(
        "SELECT COUNT(*) FROM plants"
    ).fetchone()[0]

    if plant_count == 0:

        default_plants = [
            ("Sunflower", "🌻", 30),
            ("Rose", "🌹", 50),
            ("Tulip", "🌷", 40),
            ("Cherry Blossom", "🌸", 80),
            ("Cactus", "🌵", 20),
            ("Potted Plant", "🪴", 60)
        ]

        conn.executemany("""
            INSERT INTO plants (name, emoji, cost)
            VALUES (?, ?, ?)
        """, default_plants)

    conn.commit()
    conn.close()