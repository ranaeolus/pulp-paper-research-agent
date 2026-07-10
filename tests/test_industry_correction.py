"""Regression tests for Version 0.3.1 industry interpretation and strategy quality."""

import json
from pathlib import Path

from src.database import connect_database, save_research_workflow
from src.industry_knowledge.models import InterpretationOverrides
from src.industry_knowledge.registry import interpret_request
from src.research_planner import DeterministicResearchPlanner, ResearchRequest
from src.search_strategy import generate_search_strategy


QUESTION = "分析2026—2028年越南制浆木片出口供给，以及中国新增化学浆产能对木片采购竞争和价格的影响。"


def _workflow(overrides: InterpretationOverrides | None = None):
    request = ResearchRequest(
        QUESTION, "Vietnam and China", "Woodchips → Chemical pulp", "2026–2028",
        "Procurement", "Deep research", "Chinese",
    )
    interpretation = interpret_request(request, overrides)
    plan = DeterministicResearchPlanner().generate_plan(request, interpretation)
    strategy = generate_search_strategy(request, plan, interpretation)
    return request, interpretation, plan, strategy


def test_exact_case_semantic_roles_and_geographies() -> None:
    _, interpretation, _, _ = _workflow()
    assert interpretation.primary_topic == "woodchips"
    assert interpretation.secondary_topic == "market_pulp"
    assert interpretation.supply_geography == "Vietnam"
    assert interpretation.demand_geography == "China"
    assert interpretation.decision_objective == "Procurement"
    assert interpretation.confidence >= 0.9
    assert "synonym" in interpretation.rationale


def test_specific_queries_replace_generic_paper_baselines() -> None:
    _, _, _, strategy = _workflow()
    texts = [query.query_text.casefold() for query in strategy.queries]
    assert not any("pulp paper production capacity consumption statistics" in text for text in texts)
    assert not any("paper exports imports customs trade flows" in text for text in texts)
    assert sum("woodchip" in text or "木片" in text for text in texts) >= len(texts) // 2


def test_plantation_harvest_export_port_and_shipping_queries() -> None:
    _, _, _, strategy = _workflow()
    by_dimension = {query.analytical_dimension: query.query_text for query in strategy.queries}
    assert "plantation area" in by_dimension["resource and plantation supply"] or "人工林" in by_dimension["resource and plantation supply"]
    assert "customs unit value" in " ".join(query.query_text for query in strategy.queries)
    logistics = " ".join(query.query_text for query in strategy.queries if query.analytical_dimension == "ports and logistics")
    assert "port" in logistics and "freight" in logistics


def test_china_capacity_company_and_competitor_queries() -> None:
    _, _, _, strategy = _workflow()
    texts = "\n".join(query.query_text for query in strategy.queries)
    assert "中国 新增 化学浆 产能" in texts
    assert "annual report" in texts and "environmental approval" in texts
    assert "woodchip buyers captive plantations" in texts
    assert any(query.analytical_dimension == "procurement competition" for query in strategy.queries)


def test_price_points_and_alternative_origins_are_distinct() -> None:
    _, _, plan, strategy = _workflow()
    price_question = next(item.question for item in plan.research_questions if "FOB" in item.question)
    assert all(term in price_question for term in ("FOB", "CIF", "海关单价", "到厂成本"))
    texts = " ".join(query.query_text for query in strategy.queries)
    assert all(origin in texts for origin in ("Australia", "Thailand", "Malaysia", "Indonesia", "Brazil"))


def test_procurement_frameworks_and_full_supply_chain() -> None:
    _, interpretation, plan, _ = _workflow()
    chain = " → ".join(interpretation.causal_chain)
    assert all(stage in chain for stage in ("Plantation owner", "Chip mill", "Export port", "Woodchip vessel", "Pulp mill"))
    assert all(framework in plan.analytical_frameworks for framework in ("contestable-supply analysis", "buyer demand overlap by origin and port", "delivered-cost parity"))
    assert any("contract" in item.casefold() or "合同" in item for item in plan.proposed_deliverable_structure)


def test_three_scenarios_have_required_design_fields() -> None:
    _, _, plan, _ = _workflow()
    assert [scenario.name for scenario in plan.scenario_structure] == ["基准情景", "供应偏紧/高价情景", "供应宽松/低价情景"]
    for scenario in plan.scenario_structure:
        assert scenario.assumptions and scenario.key_variables and scenario.triggers
        assert scenario.evidence_required and scenario.decision_implications


def test_queries_are_human_readable_and_dimension_focused() -> None:
    _, _, _, strategy = _workflow()
    for query in strategy.queries:
        assert query.query_text == " ".join(query.query_text.split())
        assert query.purpose and query.rationale and query.related_sub_question
        assert query.primary_or_supporting in {"primary", "supporting"}
        assert "," not in query.query_text
        assert "trade flows costs margins inventories prices" not in query.query_text.casefold()


def test_user_override_changes_primary_topic() -> None:
    _, interpretation, plan, strategy = _workflow(InterpretationOverrides("market_pulp", "woodchips", "China", "Global", "Strategy"))
    assert interpretation.primary_topic == "market_pulp"
    assert interpretation.secondary_topic == "woodchips"
    assert interpretation.supply_geography == "China"
    assert interpretation.decision_objective == "Strategy"
    assert all("paper production capacity consumption" not in query.query_text.casefold() for query in strategy.queries)
    assert plan.research_questions


def test_corrected_interpretation_is_persisted(tmp_path: Path) -> None:
    request, interpretation, plan, strategy = _workflow()
    path = tmp_path / "interpretation.db"
    request_id, _, _ = save_research_workflow(path, request, plan, strategy, interpretation)
    with connect_database(path) as connection:
        raw = connection.execute("SELECT interpretation_json FROM industry_interpretations WHERE request_id=?", (request_id,)).fetchone()[0]
    saved = json.loads(raw)
    assert saved["primary_topic"] == "woodchips"
    assert saved["supply_geography"] == "Vietnam"


def test_other_knowledge_packs_remain_topic_specific() -> None:
    cases = (
        ("未来中国白卡纸盈利能力", "paperboard", "paperboard capacity and profitability"),
        ("中国白卡纸供需", "paperboard", "paperboard supply demand"),
        ("global wet-strength-agent competitive landscape", "chemicals", "chemicals competition"),
        ("APP global chemicals strategy", "chemicals", "chemicals competition"),
        ("global hardwood market pulp price cycle", "market_pulp", "market pulp cycle"),
    )
    for question, topic, dimension in cases:
        request = ResearchRequest(question, output_language="English")
        interpretation = interpret_request(request)
        plan = DeterministicResearchPlanner().generate_plan(request, interpretation)
        strategy = generate_search_strategy(request, plan, interpretation)
        assert interpretation.primary_topic == topic
        assert any(query.analytical_dimension == dimension for query in strategy.queries)
