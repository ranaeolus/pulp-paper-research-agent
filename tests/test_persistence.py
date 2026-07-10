"""SQLite schema-upgrade and Version 0.3 persistence tests."""

import sqlite3
from pathlib import Path

from src.database import (
    complete_discovery_session, connect_database, create_discovery_session,
    initialize_database, save_research_workflow,
)
from src.research_planner import DeterministicResearchPlanner, ResearchRequest
from src.search_provider import SearchResult
from src.search_strategy import SourceCategory, generate_search_strategy


def test_schema_upgrade_and_workflow_persistence(tmp_path: Path) -> None:
    path = tmp_path / "upgrade.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute("INSERT INTO app_metadata VALUES ('schema_version', '1')")
        connection.execute("INSERT INTO app_metadata VALUES ('legacy_record', 'preserve-me')")

    initialize_database(path)
    request = ResearchRequest("越南木片供应如何变化？", output_language="Chinese")
    plan = DeterministicResearchPlanner().generate_plan(request)
    strategy = generate_search_strategy(request, plan)
    request_id, plan_id, strategy_id = save_research_workflow(path, request, plan, strategy)
    session_id = create_discovery_session(path, strategy_id)
    result = SearchResult("Official", "https://stats.gov.vn/data", "stats.gov.vn", None,
        "Data", "query", SourceCategory.GOVERNMENT, "Question", 1,
        "2026-01-01T00:00:00+00:00", 1, "Government source")
    complete_discovery_session(path, session_id, [result])

    with connect_database(path) as connection:
        assert connection.execute("SELECT value FROM app_metadata WHERE key='schema_version'").fetchone() == ("4",)
        assert connection.execute("SELECT value FROM app_metadata WHERE key='legacy_record'").fetchone() == ("preserve-me",)
        assert (request_id, plan_id, strategy_id) == (1, 1, 1)
        assert connection.execute("SELECT status FROM discovery_sessions").fetchone() == ("completed",)
        assert connection.execute("SELECT COUNT(*) FROM search_results").fetchone() == (1,)
