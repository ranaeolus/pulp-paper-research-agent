"""Deterministic bilingual web-search strategy generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum

from src.industry_knowledge.models import IndustryInterpretation
from src.industry_knowledge.registry import get_knowledge_pack, interpret_request
from src.research_planner import ResearchPlan, ResearchRequest, detect_topics


class SourceCategory(StrEnum):
    GOVERNMENT = "Government and statistics"
    TRADE = "Customs and trade data"
    COMPANY = "Company and regulatory disclosure"
    INDUSTRY = "Industry and professional research"
    NEWS = "Business and trade news"
    PORTS = "Ports and logistics"
    PRICE = "Price and cost"
    POLICY = "Policy and regulation"


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query_text: str
    purpose: str
    language: str
    priority: int
    expected_source_type: SourceCategory
    related_sub_question: str
    analytical_dimension: str = "general"
    primary_or_supporting: str = "supporting"
    rationale: str = "Supports the related research question."


@dataclass(frozen=True, slots=True)
class SearchStrategy:
    queries: tuple[SearchQuery, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def generate_search_strategy(
    request: ResearchRequest, plan: ResearchPlan,
    interpretation: IndustryInterpretation | None = None,
) -> SearchStrategy:
    """Create pack-driven, geography-role-aware professional search queries."""
    interpretation = interpretation or interpret_request(request)
    pack = get_knowledge_pack(interpretation.primary_topic)
    period = f" {request.time_horizon.strip()}" if request.time_horizon.strip() else ""
    zh_names = {"Vietnam": "越南", "China": "中国", "Global": "全球", "Southeast Asia": "东南亚", "Australia": "澳大利亚", "Brazil": "巴西"}
    values = {
        "supply": interpretation.supply_geography,
        "demand": interpretation.demand_geography,
        "supply_zh": zh_names.get(interpretation.supply_geography, interpretation.supply_geography),
        "demand_zh": zh_names.get(interpretation.demand_geography, interpretation.demand_geography),
        "topic": pack.english_name,
        "topic_zh": pack.chinese_name,
    }
    category_map = {category.value: category for category in SourceCategory}
    queries: list[SearchQuery] = []
    for index, template in enumerate(pack.query_templates):
        text = template.template.format(**values).strip() + period
        related = _related_question(plan, template.analytical_dimension)
        queries.append(SearchQuery(
            text, template.purpose, template.language, template.priority,
            category_map.get(template.source_category, SourceCategory.INDUSTRY), related,
            template.analytical_dimension, template.status,
            (f"该查询基于已识别的地理角色与主要研究对象{pack.chinese_name}，用于检验对应分析维度。" if template.language == "Chinese" else f"This {template.geography_role}-geography query tests {template.analytical_dimension} for the primary object {pack.english_name}."),
        ))
    if interpretation.primary_topic == "woodchips" and interpretation.decision_objective == "Procurement":
        queries.extend((
            SearchQuery(f"{interpretation.demand_geography} woodchip buyers captive plantations long-term contracts procurement", "Map current buyers, captive supply, and contracting exposure.", "English", 1, SourceCategory.COMPANY, _related_question(plan, "competing buyers"), "procurement competition", "primary", "Buyer structure determines contestable supply and bargaining power."),
            SearchQuery(f"{values['demand_zh']} 木片 买家 自有林 长协 现货 采购", "识别现有买家、自有供应及长协/现货敞口。", "Chinese", 1, SourceCategory.COMPANY, _related_question(plan, "竞争买家"), "procurement competition", "primary", "买家结构决定可竞争供应及议价能力。"),
            SearchQuery("woodchip buyer supplier concentration contestable supply contract spot procurement", "Find evidence for buyer/supplier concentration and contestable supply.", "English", 2, SourceCategory.INDUSTRY, _related_question(plan, "competing buyers"), "procurement strategy", "supporting", "Supports contract strategy, negotiation leverage, and security-of-supply assessment."),
            SearchQuery("木片 采购竞争 可竞争供应 供应商集中度 买家集中度 长协 现货", "查找采购竞争、集中度及合同机制证据。", "Chinese", 2, SourceCategory.INDUSTRY, _related_question(plan, "竞争买家"), "procurement strategy", "supporting", "支持合同策略、议价能力与供应安全评估。"),
            SearchQuery("woodchip base case tight supply high price loose supply low price indicators", "Identify evidence and trigger indicators for procurement scenarios.", "English", 3, SourceCategory.INDUSTRY, _related_question(plan, "scenario"), "scenario indicators", "supporting", "Scenario triggers must be evidence-backed before quantification."),
        ))
    if pack.entity_search_leads:
        leads = " OR ".join(f'"{lead}"' for lead in pack.entity_search_leads[:5])
        queries.append(SearchQuery(
            f"({leads}) annual report pulp project woodchip procurement commissioning",
            "Use explicitly provisional company leads to discover disclosures and projects.", "English", 3,
            SourceCategory.COMPANY, _related_question(plan, "competing buyers"),
            "entity discovery", "supporting",
            "Named entities are search leads only and must be verified for relevance.",
        ))
    return SearchStrategy(tuple(queries))


def _paired(
    english: str, chinese: str, english_purpose: str, chinese_purpose: str,
    category: SourceCategory, sub_question: str, priority: int,
) -> tuple[SearchQuery, SearchQuery]:
    return (
        SearchQuery(english, english_purpose, "English", priority, category, sub_question),
        SearchQuery(chinese, chinese_purpose, "Chinese", priority, category, sub_question),
    )


def _related_question(plan: ResearchPlan, keyword: str) -> str:
    key = keyword.casefold()
    return next(
        (item.question for item in plan.research_questions if any(token in item.question.casefold() for token in key.split())),
        plan.research_questions[0].question,
    )
