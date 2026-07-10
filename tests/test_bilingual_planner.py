"""Chinese terminology and bilingual deterministic planner tests."""

from src.research_planner import DeterministicResearchPlanner, ResearchRequest, detect_topics


def test_chinese_vietnam_woodchip_question() -> None:
    request = ResearchRequest(
        research_question="越南制浆木片出口供应未来五年如何变化？",
        geographic_scope="越南及中国", time_horizon="2025-2030",
        decision_context="Procurement", output_language="Chinese",
    )
    plan = DeterministicResearchPlanner().generate_plan(request)
    assert "woodchips" in detect_topics(request)
    assert any("人工林" in item.indicator for item in plan.required_data)
    assert "采购" in plan.restated_objective


def test_chinese_hardwood_pulp_price_question() -> None:
    request = ResearchRequest(
        research_question="全球阔叶浆价格和库存周期由哪些因素驱动？",
        output_language="Chinese",
    )
    plan = DeterministicResearchPlanner().generate_plan(request)
    assert "market pulp" in detect_topics(request)
    assert "costs, margins, inventories, and prices" in detect_topics(request)
    assert any("价格周期" in item for item in plan.analytical_frameworks)


def test_chinese_packaging_board_competitor_question() -> None:
    request = ResearchRequest(
        research_question="东南亚白卡纸竞争者的新增产能和成本优势如何研究？",
        output_language="Chinese",
    )
    plan = DeterministicResearchPlanner().generate_plan(request)
    assert "packaging paper and board" in detect_topics(request)
    assert "capacity additions and shutdowns" in detect_topics(request)
    assert any("竞争对标" in item for item in plan.analytical_frameworks)


def test_chinese_and_english_synonyms_map_to_same_topics() -> None:
    pairs = (
        ("人工林桉木供应", "eucalyptus plantation supply", "forestry and plantations"),
        ("OCC回收纸进口", "RCP recovered paper imports", "recovered paper"),
        ("NBSK针叶浆价格", "NBSK softwood pulp price", "market pulp"),
        ("FBB白卡纸产能", "FBB packaging board capacity", "packaging paper and board"),
    )
    for chinese, english, topic in pairs:
        assert topic in detect_topics(ResearchRequest(chinese))
        assert topic in detect_topics(ResearchRequest(english))


def test_offline_chinese_planner_is_stable() -> None:
    request = ResearchRequest("中国生活用纸需求如何研究？", output_language="Chinese")
    planner = DeterministicResearchPlanner()
    assert planner.generate_plan(request) == planner.generate_plan(request)
