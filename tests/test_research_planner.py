"""Tests for deterministic pulp and paper research planning."""

import pytest

from src.research_planner import (
    DeterministicResearchPlanner,
    ResearchRequest,
    detect_topics,
)


def test_vietnam_woodchip_supply_plan_is_topic_specific() -> None:
    request = ResearchRequest(
        research_question="How will Vietnam woodchip export supply evolve?",
        geographic_scope="Vietnam and key Asian destinations",
        value_chain_segment="Plantation woodchips",
        time_horizon="2025-2030",
        decision_context="Procurement",
    )

    plan = DeterministicResearchPlanner().generate_plan(request)

    assert "woodchips" in detect_topics(request)
    assert any("harvest" in hypothesis.lower() for hypothesis in plan.hypotheses_to_test)
    assert any("bone-dry tonnes" in item.unit for item in plan.required_data)
    assert "Vietnam" in plan.restated_objective


def test_global_hardwood_pulp_price_plan_includes_cycle_analysis() -> None:
    request = ResearchRequest(
        research_question="What variables could shape global hardwood pulp prices?",
        geographic_scope="Global",
        value_chain_segment="Market pulp",
        time_horizon="2024-2028",
        decision_context="Market intelligence",
    )

    plan = DeterministicResearchPlanner().generate_plan(request)

    assert "market pulp" in detect_topics(request)
    assert any("price-cycle" in framework.lower() for framework in plan.analytical_frameworks)
    assert any("air-dry tonne" in item.unit for item in plan.required_data)


def test_packaging_board_competitor_plan_includes_benchmarking() -> None:
    request = ResearchRequest(
        research_question="How should we assess packaging-board competitors in Southeast Asia?",
        decision_context="Competitive intelligence",
        desired_depth="Deep research",
    )

    plan = DeterministicResearchPlanner().generate_plan(request)

    assert "packaging paper and board" in detect_topics(request)
    assert any("competitor benchmarking" in framework.lower() for framework in plan.analytical_frameworks)
    assert any("competitors differ" in item.question.lower() for item in plan.research_questions)


def test_missing_optional_fields_use_explicit_defaults() -> None:
    plan = DeterministicResearchPlanner().generate_plan(
        ResearchRequest(research_question="Assess tissue demand drivers")
    )

    assert "geographies implied by the question" in plan.scope_and_boundaries[0]
    assert "latest available history" in plan.scope_and_boundaries[2]
    assert "general market understanding" in plan.restated_objective


def test_empty_research_question_is_rejected() -> None:
    with pytest.raises(ValueError, match="Research question is required"):
        ResearchRequest(research_question="   ")


def test_structured_output_is_stable() -> None:
    request = ResearchRequest(
        research_question="Assess announced containerboard capacity additions",
        geographic_scope="Europe",
        time_horizon="2026-2030",
    )
    planner = DeterministicResearchPlanner()

    first = planner.generate_plan(request)
    second = planner.generate_plan(request)

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert tuple(first.to_dict()) == (
        "restated_objective",
        "scope_and_boundaries",
        "key_definitions",
        "hypotheses_to_test",
        "research_questions",
        "required_data",
        "recommended_source_hierarchy",
        "analytical_frameworks",
        "scenario_structure",
        "risks_and_data_gaps",
        "proposed_deliverable_structure",
    )
