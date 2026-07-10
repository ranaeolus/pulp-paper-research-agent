"""Knowledge-pack registry and deterministic semantic interpretation."""

from __future__ import annotations

import re

from src.industry_knowledge.chemicals import CHEMICALS
from src.industry_knowledge.market_pulp import MARKET_PULP
from src.industry_knowledge.models import IndustryInterpretation, InterpretationOverrides, KnowledgePack
from src.industry_knowledge.paperboard import PAPERBOARD
from src.industry_knowledge.woodchips import WOODCHIPS

PACKS: dict[str, KnowledgePack] = {pack.topic_id: pack for pack in (WOODCHIPS, MARKET_PULP, PAPERBOARD, CHEMICALS)}

GEOGRAPHIES = {
    "Vietnam": ("vietnam", "越南"), "China": ("china", "中国"),
    "Global": ("global", "全球"), "Southeast Asia": ("southeast asia", "东南亚"),
    "Australia": ("australia", "澳大利亚"), "Brazil": ("brazil", "巴西"),
}


def get_knowledge_pack(topic_id: str) -> KnowledgePack:
    return PACKS.get(topic_id, PACKS["woodchips"])


def available_topics() -> tuple[str, ...]:
    return tuple(PACKS)


def interpret_request(request, overrides: InterpretationOverrides | None = None) -> IndustryInterpretation:
    """Resolve semantic topic and geography roles without external calls."""
    overrides = overrides or InterpretationOverrides()
    text = " ".join((request.research_question, request.value_chain_segment)).casefold()
    scores = {
        topic_id: sum(1 for synonym in pack.synonyms if synonym.casefold() in text)
        for topic_id, pack in PACKS.items()
    }
    if scores["woodchips"] and scores["market_pulp"]:
        primary, secondary = "woodchips", "market_pulp"
    else:
        ranked = sorted(scores, key=lambda key: (-scores[key], tuple(PACKS).index(key)))
        primary = ranked[0] if scores[ranked[0]] else "woodchips"
        secondary = next((key for key in ranked[1:] if scores[key]), "")
    primary = overrides.primary_topic or primary
    secondary = overrides.secondary_topic or secondary

    mentioned = [name for name, aliases in GEOGRAPHIES.items() if any(alias in text or alias in request.geographic_scope.casefold() for alias in aliases)]
    supply = overrides.supply_geography or ("Vietnam" if "Vietnam" in mentioned and primary == "woodchips" else (mentioned[0] if mentioned else request.geographic_scope or "To be defined"))
    demand = overrides.demand_geography or ("China" if "China" in mentioned and "China" != supply else (mentioned[1] if len(mentioned) > 1 else "To be defined"))
    decision = overrides.decision_context or request.decision_context or "Market intelligence"
    pack = get_knowledge_pack(primary)
    confidence = 0.95 if scores.get(primary, 0) >= 2 and (primary != "woodchips" or "木片" in text or "woodchip" in text) else 0.75
    reason_parts = [f"Primary topic matched {scores.get(primary, 0)} declared synonym(s)."]
    if secondary:
        reason_parts.append(f"Secondary topic matched {scores.get(secondary, 0)} synonym(s) and is treated as a causal demand or value-chain factor.")
    if overrides != InterpretationOverrides():
        reason_parts.append("User overrides were applied to the semantic interpretation.")
    relationship = f"{pack.english_name} supply in {supply} serves downstream {get_knowledge_pack(secondary).english_name if secondary else 'demand'} in {demand}."
    return IndustryInterpretation(
        primary, secondary, pack.upstream_topics, pack.downstream_topics, decision,
        supply, demand, relationship, pack.value_chain_stages,
        pack.scenario_variables, confidence, " ".join(reason_parts),
    )
