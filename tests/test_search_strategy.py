"""Tests for targeted bilingual search-query generation."""

from src.research_planner import DeterministicResearchPlanner, ResearchRequest
from src.search_strategy import generate_search_strategy


def test_search_strategy_generates_chinese_and_english_queries() -> None:
    request = ResearchRequest(
        "越南木片出口供应是否可持续？", geographic_scope="越南",
        time_horizon="2025-2030", output_language="Chinese",
    )
    plan = DeterministicResearchPlanner().generate_plan(request)
    strategy = generate_search_strategy(request, plan)
    languages = {query.language for query in strategy.queries}
    assert languages == {"Chinese", "English"}
    assert all(query.purpose and query.related_sub_question for query in strategy.queries)
    assert any("woodchip" in query.query_text for query in strategy.queries)
    assert any("木片" in query.query_text for query in strategy.queries)
