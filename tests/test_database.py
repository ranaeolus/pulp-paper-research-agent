"""Tests for database infrastructure."""

from pathlib import Path

from src.database import connect_database, initialize_database


def test_initialize_database_creates_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "test.db"

    initialize_database(database_path)

    assert database_path.exists()
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'schema_version'"
        ).fetchone()
    assert row == ("3",)
