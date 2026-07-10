"""Typed, deterministic research planning for the pulp and paper value chain."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """User inputs that define a research-planning task."""

    research_question: str
    geographic_scope: str = ""
    value_chain_segment: str = ""
    time_horizon: str = ""
    decision_context: str = ""
    desired_depth: str = "Standard research"

    def __post_init__(self) -> None:
        if not self.research_question.strip():
            raise ValueError("Research question is required.")


@dataclass(frozen=True, slots=True)
class ResearchSubQuestion:
    """A research question with the variables needed to investigate it."""

    question: str
    variables: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DataRequirement:
    """A fact set to collect, including measurement expectations."""

    indicator: str
    purpose: str
    unit: str
    time_period: str
    dimensions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    """Structured output describing how a question should be researched."""

    restated_objective: str
    scope_and_boundaries: tuple[str, ...]
    key_definitions: tuple[str, ...]
    hypotheses_to_test: tuple[str, ...]
    research_questions: tuple[ResearchSubQuestion, ...]
    required_data: tuple[DataRequirement, ...]
    recommended_source_hierarchy: tuple[str, ...]
    analytical_frameworks: tuple[str, ...]
    risks_and_data_gaps: tuple[str, ...]
    proposed_deliverable_structure: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a stable serialization suitable for UI or persistence."""
        return asdict(self)


class ResearchPlanner(Protocol):
    """Interface implemented by local and future LLM-backed planners."""

    def generate_plan(self, request: ResearchRequest) -> ResearchPlan:
        """Create a research plan without answering the research question."""


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "forestry and plantations": ("forest", "forestry", "plantation", "eucalyptus", "acacia"),
    "woodchips": ("woodchip", "wood chip", "chips"),
    "recovered paper": ("recovered paper", "waste paper", "occ", "rccm"),
    "market pulp": ("market pulp", "hardwood pulp", "softwood pulp", "bskp", "bep", "pulp price"),
    "integrated pulp and paper": ("integrated pulp", "integrated mill", "pulp and paper mill"),
    "packaging paper and board": ("packaging", "containerboard", "packaging board", "cartonboard", "linerboard", "boxboard"),
    "printing and writing paper": ("printing paper", "writing paper", "uncoated freesheet", "coated paper"),
    "tissue": ("tissue", "toilet paper", "facial tissue"),
    "specialty paper": ("specialty paper", "speciality paper", "thermal paper", "release liner"),
    "pulp and paper chemicals": ("paper chemicals", "pulp chemicals", "caustic soda", "starch", "latex"),
    "biomass and energy": ("biomass", "energy", "power", "black liquor", "recovery boiler"),
    "logistics, ports, and shipping": ("logistics", "port", "shipping", "freight", "vessel"),
    "trade flows": ("trade", "export", "import", "shipment", "customs"),
    "capacity additions and shutdowns": ("capacity", "new mill", "addition", "shutdown", "closure", "conversion"),
    "costs, margins, inventories, and prices": ("cost", "margin", "inventory", "inventories", "price", "profitability"),
}


def detect_topics(request: ResearchRequest) -> tuple[str, ...]:
    """Identify relevant value-chain topics in deterministic declaration order."""
    text = " ".join(
        (request.research_question, request.value_chain_segment)
    ).casefold()
    return tuple(
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ) or ("general pulp and paper market",)


class DeterministicResearchPlanner:
    """Offline rule-based planner that produces a topic-specific baseline plan."""

    _source_hierarchy = (
        "Tier 1 — government statistics, customs data, regulators, and official policy documents",
        "Tier 2 — company filings, investor materials, mill announcements, and port disclosures",
        "Tier 3 — industry associations, recognized price-reporting agencies, and technical institutes",
        "Tier 4 — reputable trade press and specialist research; use for leads and triangulation",
        "Tier 5 — secondary summaries; do not rely on them for material claims without corroboration",
    )

    def generate_plan(self, request: ResearchRequest) -> ResearchPlan:
        topics = detect_topics(request)
        geography = request.geographic_scope.strip() or "geographies implied by the question"
        horizon = request.time_horizon.strip() or "latest available history and a clearly stated forward period"
        segment = request.value_chain_segment.strip() or ", ".join(topics)
        context = request.decision_context.strip() or "general market understanding"

        return ResearchPlan(
            restated_objective=(
                f"Develop an evidence-based research approach to evaluate: "
                f"{request.research_question.strip()} The work will support {context.lower()} "
                "without treating unverified assumptions as findings."
            ),
            scope_and_boundaries=(
                f"Geographic scope: {geography}.",
                f"Product/value-chain scope: {segment}.",
                f"Time horizon: {horizon}; label historical actuals, estimates, and forecasts separately.",
                f"Depth: {request.desired_depth}; prioritize material decision variables over exhaustive coverage.",
                "Exclude unsupported forecasts and distinguish announced, financed, under-construction, and operating capacity.",
            ),
            key_definitions=self._definitions(topics),
            hypotheses_to_test=self._hypotheses(topics, geography),
            research_questions=self._sub_questions(topics),
            required_data=self._data_requirements(topics, horizon),
            recommended_source_hierarchy=self._source_hierarchy,
            analytical_frameworks=self._frameworks(topics),
            risks_and_data_gaps=self._risks(topics),
            proposed_deliverable_structure=(
                "Executive summary: verified findings, implications, and confidence levels",
                "Scope, definitions, methodology, units, currencies, and source-quality notes",
                "Market and value-chain evidence organized around the key research questions",
                "Hypothesis assessment: supported, rejected, or unresolved",
                "Scenarios, sensitivities, and decision implications where evidence permits",
                "Risks, data gaps, monitoring indicators, and source appendix",
            ),
        )

    @staticmethod
    def _definitions(topics: tuple[str, ...]) -> tuple[str, ...]:
        definitions = [f"Define the included boundary for {topic}." for topic in topics]
        if "capacity additions and shutdowns" in topics:
            definitions.append("Separate nameplate capacity from effective production and commercial ramp-up.")
        if "costs, margins, inventories, and prices" in topics:
            definitions.append("Specify price basis, grade, currency, delivery terms, unit, and nominal versus real values.")
        if "trade flows" in topics:
            definitions.append("Specify customs codes, origin/destination, gross versus net weight, and reporting lag.")
        return tuple(definitions)

    @staticmethod
    def _hypotheses(topics: tuple[str, ...], geography: str) -> tuple[str, ...]:
        hypotheses = [
            f"Supply availability in {geography} is materially influenced by capacity, utilization, and operating constraints.",
            "Observed market outcomes can be explained by separately testing supply, demand, trade, cost, inventory, price, and policy variables.",
        ]
        if "woodchips" in topics:
            hypotheses.append("Woodchip export availability is constrained by harvest economics, plantation maturity, domestic demand, and port logistics.")
        if "market pulp" in topics:
            hypotheses.append("Pulp price direction is associated with producer inventories, operating rates, cost-curve shifts, and downstream demand rather than a single driver.")
        if "packaging paper and board" in topics:
            hypotheses.append("Competitor advantage differs by delivered cost, product mix, integration, customer access, and capacity ramp-up quality.")
        return tuple(hypotheses)

    @staticmethod
    def _sub_questions(topics: tuple[str, ...]) -> tuple[ResearchSubQuestion, ...]:
        questions = [
            ResearchSubQuestion("What is the current and historical supply-demand balance?", ("capacity", "production", "operating rate", "consumption")),
            ResearchSubQuestion("How do trade flows and policy alter regional availability?", ("imports", "exports", "tariffs", "regulation")),
            ResearchSubQuestion("Which cost, inventory, and price mechanisms matter most?", ("cash cost", "freight", "inventory", "benchmark price")),
        ]
        if "woodchips" in topics:
            questions.append(ResearchSubQuestion("How sustainable and expandable is woodchip supply?", ("plantation area", "harvest cycle", "yield", "domestic use", "port throughput")))
        if "market pulp" in topics:
            questions.append(ResearchSubQuestion("What drives the relevant pulp benchmark and its cycle?", ("grade spread", "producer stocks", "downtime", "paper demand", "FX")))
        if "packaging paper and board" in topics:
            questions.append(ResearchSubQuestion("How do competitors differ in position and likely conduct?", ("mill footprint", "grade mix", "integration", "customers", "announced capacity")))
        return tuple(questions)

    @staticmethod
    def _data_requirements(topics: tuple[str, ...], horizon: str) -> tuple[DataRequirement, ...]:
        data = [
            DataRequirement("Capacity, production, and operating rate", "Measure effective supply", "tonnes/year; tonnes; percent", horizon, ("country", "company", "mill", "grade")),
            DataRequirement("Demand and consumption", "Measure end-market pull", "tonnes; year-over-year percent", horizon, ("country", "end use", "grade")),
            DataRequirement("Trade flows", "Reconcile regional availability", "tonnes and value in stated currency", horizon, ("origin", "destination", "customs code")),
            DataRequirement("Costs, inventories, and prices", "Test economics and cycle signals", "currency/tonne; inventory days or tonnes", horizon, ("grade", "region", "delivery basis", "currency")),
        ]
        if "woodchips" in topics:
            data.append(DataRequirement("Plantation and woodchip supply", "Assess sustainable exportable volume", "hectares; m³/ha/year; bone-dry tonnes", horizon, ("species", "age class", "province", "port")))
        if "market pulp" in topics:
            data.append(DataRequirement("Pulp benchmark series", "Separate grade and regional price effects", "currency/air-dry tonne", horizon, ("hardwood/softwood", "benchmark", "delivery terms")))
        if "packaging paper and board" in topics:
            data.append(DataRequirement("Competitor asset and product profile", "Compare strategic position", "tonnes/year; cash cost/tonne; market share percent", horizon, ("company", "mill", "grade", "customer region")))
        return tuple(data)

    @staticmethod
    def _frameworks(topics: tuple[str, ...]) -> tuple[str, ...]:
        frameworks = [
            "Supply-demand balance with explicit reconciliation of production, consumption, and net trade",
            "Cost curve and delivered-cost comparison with common currency, unit, and freight basis",
            "Driver tree separating supply, demand, trade, cost, inventory, price, and policy variables",
        ]
        if "woodchips" in topics:
            frameworks.append("Biological supply bridge: plantation area × harvestable share × yield × recovery rate")
        if "market pulp" in topics:
            frameworks.append("Price-cycle analysis linking inventories, utilization, downtime, grade spreads, and downstream demand")
        if "packaging paper and board" in topics:
            frameworks.append("Competitor benchmarking across assets, integration, cost, product mix, customers, and announced moves")
        return tuple(frameworks)

    @staticmethod
    def _risks(topics: tuple[str, ...]) -> tuple[str, ...]:
        risks = [
            "Public data may differ in product definition, unit, currency, calendar basis, or revision status.",
            "Private-company production, cost, inventory, and customer data may be unavailable and require triangulation.",
            "Announcements may not represent funded projects, achieved ramp-up, or effective capacity.",
            "Forecasts are scenario-dependent; document assumptions and confidence rather than presenting them as facts.",
        ]
        if "trade flows" in topics:
            risks.append("Customs-code aggregation, transshipment, and reporting lags may obscure actual trade flows.")
        if "forestry and plantations" in topics or "woodchips" in topics:
            risks.append("Plantation age class, ownership, certification, weather, and illegal-harvest data may be incomplete.")
        return tuple(risks)


class LLMResearchPlanner:
    """Reserved interface implementation for a future LLM integration."""

    def generate_plan(self, request: ResearchRequest) -> ResearchPlan:
        raise NotImplementedError("LLM-backed planning is not implemented in Version 0.2.")
