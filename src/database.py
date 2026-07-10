"""SQLite connection and schema initialization utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = "1"


def connect_database(database_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection configured for reliable local persistence."""
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    """Create the database and Version 0.1 metadata schema if needed."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect_database(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO app_metadata (key, value)
            VALUES ('schema_version', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (SCHEMA_VERSION,),
        )
