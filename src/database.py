"""SQLite connection and schema initialization utilities."""

from __future__ import annotations

import sqlite3
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "4"


def connect_database(database_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection configured for reliable local persistence."""
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    """Create or upgrade the database without removing prior records."""
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
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                request_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS research_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES research_requests(id)
            );
            CREATE TABLE IF NOT EXISTS industry_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                interpretation_json TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES research_requests(id)
            );
            CREATE TABLE IF NOT EXISTS search_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                strategy_json TEXT NOT NULL,
                FOREIGN KEY(request_id) REFERENCES research_requests(id),
                FOREIGN KEY(plan_id) REFERENCES research_plans(id)
            );
            CREATE TABLE IF NOT EXISTS discovery_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY(strategy_id) REFERENCES search_strategies(id)
            );
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                result_json TEXT NOT NULL,
                normalized_url TEXT NOT NULL,
                source_domain TEXT NOT NULL,
                source_tier INTEGER NOT NULL,
                FOREIGN KEY(session_id) REFERENCES discovery_sessions(id),
                UNIQUE(session_id, normalized_url)
            );
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


def save_research_workflow(
    database_path: Path, request: Any, plan: Any, strategy: Any,
    interpretation: Any | None = None,
) -> tuple[int, int, int]:
    """Persist a request, generated plan, and search strategy atomically."""
    initialize_database(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with connect_database(database_path) as connection:
        request_cursor = connection.execute(
            "INSERT INTO research_requests(created_at, request_json) VALUES (?, ?)",
            (now, json.dumps(asdict(request), ensure_ascii=False)),
        )
        request_id = int(request_cursor.lastrowid)
        if interpretation is not None:
            connection.execute(
                "INSERT INTO industry_interpretations(request_id, created_at, interpretation_json) VALUES (?, ?, ?)",
                (request_id, now, json.dumps(interpretation.to_dict(), ensure_ascii=False)),
            )
        plan_cursor = connection.execute(
            "INSERT INTO research_plans(request_id, created_at, plan_json) VALUES (?, ?, ?)",
            (request_id, now, json.dumps(plan.to_dict(), ensure_ascii=False)),
        )
        plan_id = int(plan_cursor.lastrowid)
        strategy_cursor = connection.execute(
            "INSERT INTO search_strategies(request_id, plan_id, created_at, strategy_json) VALUES (?, ?, ?, ?)",
            (request_id, plan_id, now, json.dumps(strategy.to_dict(), ensure_ascii=False)),
        )
        return request_id, plan_id, int(strategy_cursor.lastrowid)


def create_discovery_session(
    database_path: Path, strategy_id: int, status: str = "running"
) -> int:
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO discovery_sessions(strategy_id, created_at, status) VALUES (?, ?, ?)",
            (strategy_id, datetime.now(timezone.utc).isoformat(), status),
        )
        return int(cursor.lastrowid)


def complete_discovery_session(
    database_path: Path, session_id: int, results: list[Any],
    status: str = "completed", error_message: str | None = None,
) -> None:
    """Persist normalized candidates and final session state atomically."""
    with connect_database(database_path) as connection:
        for result in results:
            connection.execute(
                """
                INSERT OR IGNORE INTO search_results(
                    session_id, created_at, result_json, normalized_url,
                    source_domain, source_tier
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, datetime.now(timezone.utc).isoformat(),
                    json.dumps(result.to_dict(), ensure_ascii=False), result.url,
                    result.source_domain, result.source_tier,
                ),
            )
        connection.execute(
            "UPDATE discovery_sessions SET status = ?, error_message = ? WHERE id = ?",
            (status, error_message, session_id),
        )
