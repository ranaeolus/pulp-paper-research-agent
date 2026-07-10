"""Typed structures for maintainable industry research guidance."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class IndicatorGuide:
    name: str
    unit: str
    purpose: str


@dataclass(frozen=True, slots=True)
class QueryTemplate:
    language: str
    geography_role: str
    analytical_dimension: str
    template: str
    purpose: str
    source_category: str
    priority: int = 2
    status: str = "primary"


@dataclass(frozen=True, slots=True)
class KnowledgePack:
    topic_id: str
    english_name: str
    chinese_name: str
    synonyms: tuple[str, ...]
    upstream_topics: tuple[str, ...]
    downstream_topics: tuple[str, ...]
    value_chain_stages: tuple[str, ...]
    analytical_dimensions: tuple[str, ...]
    indicators: tuple[IndicatorGuide, ...]
    price_points: tuple[str, ...]
    source_categories: tuple[str, ...]
    entity_categories: tuple[str, ...]
    infrastructure_categories: tuple[str, ...]
    causal_mechanisms: tuple[str, ...]
    frameworks: tuple[str, ...]
    query_templates: tuple[QueryTemplate, ...]
    hypotheses: tuple[str, ...]
    data_quality_risks: tuple[str, ...]
    scenario_variables: tuple[str, ...]
    decision_adaptations: dict[str, tuple[str, ...]]
    entity_search_leads: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InterpretationOverrides:
    primary_topic: str = ""
    secondary_topic: str = ""
    supply_geography: str = ""
    demand_geography: str = ""
    decision_context: str = ""


@dataclass(frozen=True, slots=True)
class IndustryInterpretation:
    primary_topic: str
    secondary_topic: str
    upstream_topics: tuple[str, ...]
    downstream_topics: tuple[str, ...]
    decision_objective: str
    supply_geography: str
    demand_geography: str
    value_chain_relationship: str
    causal_chain: tuple[str, ...]
    causal_variables: tuple[str, ...]
    confidence: float
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
