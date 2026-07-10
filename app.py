import streamlit as st
from dataclasses import replace

from src.config import get_settings
from src.database import (
    complete_discovery_session,
    create_discovery_session,
    initialize_database,
    save_research_workflow,
)
from src.logging_config import configure_logging
from src.industry_knowledge.models import InterpretationOverrides
from src.industry_knowledge.registry import PACKS, interpret_request
from src.research_planner import (
    DeterministicResearchPlanner,
    ResearchPlan,
    ResearchRequest,
)
from src.search_provider import (
    SearchProviderError,
    TavilySearchProvider,
    discover_sources,
)
from src.search_strategy import SearchStrategy, generate_search_strategy


DECISION_CONTEXTS = (
    "Market intelligence",
    "Strategy",
    "Investment",
    "Supply chain",
    "Procurement",
    "Competitive intelligence",
    "Executive briefing",
)
RESEARCH_DEPTHS = ("Rapid scan", "Standard research", "Deep research")
OUTPUT_LANGUAGES = ("Chinese", "English", "Bilingual")

SECTION_HEADINGS = {
    "English": (
        "Restated research objective", "Scope and boundaries", "Key definitions",
        "Key hypotheses to test", "Research questions and sub-questions",
        "Required data and indicators", "Recommended source hierarchy",
        "Analytical frameworks", "Known risks and possible data gaps",
        "Proposed final deliverable structure",
    ),
    "Chinese": (
        "重述研究目标", "范围与边界", "关键定义", "待检验的核心假设", "研究问题与子问题",
        "所需数据与指标", "建议的来源层级", "分析框架", "已知风险与潜在数据缺口", "建议的最终交付结构",
    ),
    "Bilingual": (
        "重述研究目标 / Restated research objective", "范围与边界 / Scope and boundaries",
        "关键定义 / Key definitions", "待检验的核心假设 / Key hypotheses to test",
        "研究问题与子问题 / Research questions and sub-questions",
        "所需数据与指标 / Required data and indicators",
        "建议的来源层级 / Recommended source hierarchy", "分析框架 / Analytical frameworks",
        "风险与数据缺口 / Risks and data gaps", "交付结构 / Deliverable structure",
    ),
}


def render_research_plan(plan: ResearchPlan, language: str) -> None:
    """Render a structured research plan without embedding planning logic."""
    headings = SECTION_HEADINGS[language]
    st.subheader(f"1. {headings[0]}")
    st.write(plan.restated_objective)

    sections = (
        (f"2. {headings[1]}", plan.scope_and_boundaries),
        (f"3. {headings[2]}", plan.key_definitions),
        (f"4. {headings[3]}", plan.hypotheses_to_test),
    )
    for title, items in sections:
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")

    st.subheader(f"5. {headings[4]}")
    for item in plan.research_questions:
        st.markdown(f"- **{item.question}** Variables: {', '.join(item.variables)}.")

    st.subheader(f"6. {headings[5]}")
    for item in plan.required_data:
        st.markdown(
            f"- **{item.indicator}:** {item.purpose}. Unit: {item.unit}. "
            f"Period: {item.time_period}. Dimensions: {', '.join(item.dimensions)}."
        )

    trailing_sections = (
        (f"7. {headings[6]}", plan.recommended_source_hierarchy),
        (f"8. {headings[7]}", plan.analytical_frameworks),
        (f"9. {headings[8]}", plan.risks_and_data_gaps),
        (f"10. {headings[9]}", plan.proposed_deliverable_structure),
    )
    for title, items in trailing_sections:
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")

    if plan.scenario_structure:
        scenario_title = "情景设计" if language == "Chinese" else (
            "情景设计 / Scenario design" if language == "Bilingual" else "Scenario design"
        )
        st.subheader(f"8A. {scenario_title}")
        for scenario in plan.scenario_structure:
            st.markdown(f"- **{scenario.name}**")
            st.write(f"Assumptions / 假设: {'; '.join(scenario.assumptions)}")
            st.write(f"Key variables / 关键变量: {', '.join(scenario.key_variables)}")
            st.write(f"Triggers / 触发因素: {'; '.join(scenario.triggers)}")
            st.write(f"Evidence / 所需证据: {', '.join(scenario.evidence_required)}")
            st.write(f"Implications / 采购含义: {'; '.join(scenario.decision_implications)}")


def render_research_planner(database_path) -> None:
    """Render the offline Research Planner form and its latest result."""
    st.header("Research Planner")
    st.write(
        "Define how an industry question should be researched. Version 0.3 creates "
        "a structured plan locally; it does not answer the question or call an API."
    )

    with st.form("research_planner_form"):
        research_question = st.text_area("Research question *")
        geographic_scope = st.text_input("Geographic scope (optional)")
        value_chain_segment = st.text_input(
            "Product or value-chain segment (optional)"
        )
        time_horizon = st.text_input("Time horizon (optional)")
        decision_context = st.selectbox(
            "Decision context (optional)", ("Not specified",) + DECISION_CONTEXTS
        )
        desired_depth = st.selectbox(
            "Desired depth", RESEARCH_DEPTHS, index=1
        )
        output_language = st.selectbox(
            "Output language / 输出语言", OUTPUT_LANGUAGES, index=0
        )
        submitted = st.form_submit_button("Generate Research Plan", type="primary")

    if submitted:
        try:
            request = ResearchRequest(
                research_question=research_question,
                geographic_scope=geographic_scope,
                value_chain_segment=value_chain_segment,
                time_horizon=time_horizon,
                decision_context=(
                    "" if decision_context == "Not specified" else decision_context
                ),
                desired_depth=desired_depth,
                output_language=output_language,
            )
            interpretation = interpret_request(request)
            plan = DeterministicResearchPlanner().generate_plan(request, interpretation)
            strategy = generate_search_strategy(request, plan, interpretation)
            _, _, strategy_id = save_research_workflow(
                database_path, request, plan, strategy, interpretation
            )
            st.session_state.update(
                research_request=request, research_plan=plan,
                search_strategy=strategy, strategy_id=strategy_id,
                industry_interpretation=interpretation,
                source_results=[], output_language=output_language,
            )
        except ValueError as error:
            st.error(str(error))

    if "research_plan" in st.session_state:
        st.divider()
        render_research_plan(
            st.session_state["research_plan"],
            st.session_state.get("output_language", "Chinese"),
        )


def render_source_discovery(settings) -> None:
    """Review a strategy and run bounded Tavily candidate discovery."""
    st.header("Source Discovery")
    st.info(
        "Source discovery identifies candidate evidence. It does not by itself "
        "verify that every claim or number is correct."
    )
    strategy: SearchStrategy | None = st.session_state.get("search_strategy")
    if strategy is None:
        st.write("Generate a research plan first to create a bilingual search strategy.")
        return

    interpretation = st.session_state["industry_interpretation"]
    st.subheader("Industry interpretation")
    col1, col2 = st.columns(2)
    col1.markdown(f"**Primary research object:** {interpretation.primary_topic}")
    col1.markdown(f"**Secondary object:** {interpretation.secondary_topic or 'None detected'}")
    col1.markdown(f"**Supply geography:** {interpretation.supply_geography}")
    col1.markdown(f"**Demand geography:** {interpretation.demand_geography}")
    col2.markdown(f"**Decision objective:** {interpretation.decision_objective}")
    col2.markdown(f"**Value-chain relationship:** {interpretation.value_chain_relationship}")
    col2.markdown(f"**Detection confidence:** {interpretation.confidence:.0%}")
    col2.markdown(f"**Detection rationale:** {interpretation.rationale}")
    st.markdown(f"**Value chain:** {' → '.join(interpretation.causal_chain)}")

    with st.expander("Edit interpretation and regenerate"):
        with st.form("interpretation_override_form"):
            topic_ids = tuple(PACKS)
            primary = st.selectbox("Primary topic", topic_ids, index=topic_ids.index(interpretation.primary_topic))
            secondary_options = ("",) + topic_ids
            secondary = st.selectbox("Secondary topic", secondary_options, index=secondary_options.index(interpretation.secondary_topic) if interpretation.secondary_topic in secondary_options else 0)
            supply = st.text_input("Supply geography", interpretation.supply_geography)
            demand = st.text_input("Demand geography", interpretation.demand_geography)
            context = st.selectbox("Decision objective", DECISION_CONTEXTS, index=DECISION_CONTEXTS.index(interpretation.decision_objective) if interpretation.decision_objective in DECISION_CONTEXTS else 0)
            regenerate = st.form_submit_button("Apply Overrides and Regenerate")
        if regenerate:
            request = replace(st.session_state["research_request"], decision_context=context)
            corrected = interpret_request(request, InterpretationOverrides(primary, secondary, supply, demand, context))
            plan = DeterministicResearchPlanner().generate_plan(request, corrected)
            strategy = generate_search_strategy(request, plan, corrected)
            _, _, strategy_id = save_research_workflow(settings.database_path, request, plan, strategy, corrected)
            st.session_state.update(research_request=request, research_plan=plan, search_strategy=strategy, strategy_id=strategy_id, industry_interpretation=corrected, source_results=[])
            st.rerun()

    st.subheader("Proposed search strategy")
    for query in strategy.queries:
        st.markdown(
            f"**P{query.priority} · {query.primary_or_supporting} · {query.language} · "
            f"{query.analytical_dimension} · {query.expected_source_type.value}**  \n"
            f"`{query.query_text}`  \n{query.purpose}  \n_Rationale: {query.rationale}_"
        )

    provider = TavilySearchProvider(api_key=settings.tavily_api_key)
    if not provider.configured:
        st.warning(
            "TAVILY_API_KEY is not configured. Source discovery is unavailable, "
            "but bilingual planning and query generation remain fully usable offline."
        )
    if st.button("Start Web Discovery", disabled=not provider.configured):
        session_id = create_discovery_session(
            settings.database_path, st.session_state["strategy_id"]
        )
        try:
            with st.spinner("Discovering candidate sources..."):
                results = discover_sources(
                    provider, strategy.queries, settings.max_search_queries,
                    settings.max_results_per_query,
                )
            complete_discovery_session(settings.database_path, session_id, results)
            st.session_state["source_results"] = results
        except SearchProviderError as error:
            complete_discovery_session(
                settings.database_path, session_id, [], "failed", str(error)
            )
            st.error(str(error))

    results = st.session_state.get("source_results", [])
    if results:
        st.subheader(f"Candidate sources ({len(results)})")
        grouped: dict[tuple[str, int, str], list] = {}
        for result in results:
            key = (
                result.related_sub_question, result.source_tier,
                result.expected_source_category.value,
            )
            grouped.setdefault(key, []).append(result)
        for (sub_question, tier, category), items in grouped.items():
            st.markdown(f"### {sub_question} — Tier {tier} — {category}")
            for result in items:
                st.markdown(f"**[{result.title}]({result.url})**")
                st.caption(
                    f"{result.source_domain} · {result.detected_date or 'Date unavailable'} "
                    f"· rank {result.search_rank}"
                )
                st.write(result.classification_rationale)
                st.write(f"Query: {result.originating_query}")
                st.write(result.snippet or "No snippet available.")


def main() -> None:
    """Render the Version 0.3 application."""
    settings = get_settings()
    logger = configure_logging(settings)
    initialize_database(settings.database_path)
    logger.info("Application homepage initialized")

    st.set_page_config(
        page_title=settings.app_name,
        page_icon="📊",
        layout="wide",
    )

    st.title(settings.app_name)
    st.caption("Version 0.3.1")

    home_tab, planner_tab, discovery_tab = st.tabs(
        ("Home", "Research Planner", "Source Discovery")
    )
    with home_tab:
        st.header("Status")
        st.success("Version 0.3.1 industry-aware planning and source discovery are operational.")
        st.write(
            "The application generates structured research plans locally and can discover "
            "candidate web sources through Tavily. It does not verify claims or generate findings."
        )

        st.header("Architecture")
        architecture = {
            "User interface": "Streamlit application shell",
            "Planning": "Typed deterministic industry research planner",
            "Discovery": "Bilingual search strategy and provider-neutral source normalization",
            "Configuration": "Environment-based typed settings",
            "Persistence": "SQLite initialization and schema management",
            "Observability": "Console and rotating-file logging",
            "Quality": "pytest test suite",
        }
        for component, description in architecture.items():
            st.markdown(f"- **{component}:** {description}")

        st.header("Future Modules")
        st.markdown(
            """
- Industry research orchestration
- Anthropic Claude analysis
- PDF document ingestion with PyMuPDF
- Evidence management and citations
- Market, supply-chain, investment, and strategy analysis
- Executive reports and decision-support workflows
"""
        )

    with planner_tab:
        render_research_planner(settings.database_path)

    with discovery_tab:
        render_source_discovery(settings)


if __name__ == "__main__":
    main()
