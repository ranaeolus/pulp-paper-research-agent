import streamlit as st

from src.config import get_settings
from src.database import initialize_database
from src.logging_config import configure_logging
from src.research_planner import (
    DeterministicResearchPlanner,
    ResearchPlan,
    ResearchRequest,
)


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


def render_research_plan(plan: ResearchPlan) -> None:
    """Render a structured research plan without embedding planning logic."""
    st.subheader("1. Restated research objective")
    st.write(plan.restated_objective)

    sections = (
        ("2. Scope and boundaries", plan.scope_and_boundaries),
        ("3. Key definitions", plan.key_definitions),
        ("4. Key hypotheses to test", plan.hypotheses_to_test),
    )
    for title, items in sections:
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")

    st.subheader("5. Research questions and sub-questions")
    for item in plan.research_questions:
        st.markdown(f"- **{item.question}** Variables: {', '.join(item.variables)}.")

    st.subheader("6. Required data and indicators")
    for item in plan.required_data:
        st.markdown(
            f"- **{item.indicator}:** {item.purpose}. Unit: {item.unit}. "
            f"Period: {item.time_period}. Dimensions: {', '.join(item.dimensions)}."
        )

    trailing_sections = (
        ("7. Recommended source hierarchy", plan.recommended_source_hierarchy),
        ("8. Analytical frameworks", plan.analytical_frameworks),
        ("9. Known risks and possible data gaps", plan.risks_and_data_gaps),
        ("10. Proposed final deliverable structure", plan.proposed_deliverable_structure),
    )
    for title, items in trailing_sections:
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")


def render_research_planner() -> None:
    """Render the offline Research Planner form and its latest result."""
    st.header("Research Planner")
    st.write(
        "Define how an industry question should be researched. Version 0.2 creates "
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
            )
            st.session_state["research_plan"] = (
                DeterministicResearchPlanner().generate_plan(request)
            )
        except ValueError as error:
            st.error(str(error))

    if "research_plan" in st.session_state:
        st.divider()
        render_research_plan(st.session_state["research_plan"])


def main() -> None:
    """Render the Version 0.1 application homepage."""
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
    st.caption("Version 0.2")

    home_tab, planner_tab = st.tabs(("Home", "Research Planner"))
    with home_tab:
        st.header("Status")
        st.success("Version 0.2 Research Planner is operational.")
        st.write(
            "The application generates structured research plans locally. It does not "
            "perform research, retrieve sources, or generate findings."
        )

        st.header("Architecture")
        architecture = {
            "User interface": "Streamlit application shell",
            "Planning": "Typed deterministic industry research planner",
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
- Tavily source discovery
- PDF document ingestion with PyMuPDF
- Evidence management and citations
- Market, supply-chain, investment, and strategy analysis
- Executive reports and decision-support workflows
"""
        )

    with planner_tab:
        render_research_planner()


if __name__ == "__main__":
    main()
