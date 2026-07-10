"""Deterministic bilingual web-search strategy generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum

from src.research_planner import ResearchPlan, ResearchRequest, detect_topics


class SourceCategory(StrEnum):
    GOVERNMENT = "Government and statistics"
    TRADE = "Customs and trade data"
    COMPANY = "Company and regulatory disclosure"
    INDUSTRY = "Industry and professional research"
    NEWS = "Business and trade news"


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query_text: str
    purpose: str
    language: str
    priority: int
    expected_source_type: SourceCategory
    related_sub_question: str


@dataclass(frozen=True, slots=True)
class SearchStrategy:
    queries: tuple[SearchQuery, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def generate_search_strategy(
    request: ResearchRequest, plan: ResearchPlan
) -> SearchStrategy:
    """Create targeted Chinese and English queries for detected topics."""
    topics = detect_topics(request)
    geography = request.geographic_scope.strip() or request.research_question.strip()
    horizon = request.time_horizon.strip()
    period = f" {horizon}" if horizon else ""
    primary_question = plan.research_questions[0].question
    queries: list[SearchQuery] = [
        SearchQuery(
            f"{geography} pulp paper production capacity consumption statistics{period}",
            "Establish supply, production, capacity, and demand baselines.", "English", 1,
            SourceCategory.GOVERNMENT, primary_question,
        ),
        SearchQuery(
            f"{geography} 纸浆 造纸 产量 产能 消费量 统计{period}",
            "建立供应、产量、产能与需求基线。", "Chinese", 1,
            SourceCategory.GOVERNMENT, primary_question,
        ),
        SearchQuery(
            f"{geography} pulp paper exports imports customs trade flows{period}",
            "Quantify exports, imports, and trade-flow changes.", "English", 2,
            SourceCategory.TRADE, plan.research_questions[min(1, len(plan.research_questions) - 1)].question,
        ),
        SearchQuery(
            f"{geography} 纸浆 纸制品 出口 进口 海关 贸易流{period}",
            "量化进出口及贸易流变化。", "Chinese", 2,
            SourceCategory.TRADE, plan.research_questions[min(1, len(plan.research_questions) - 1)].question,
        ),
    ]
    topic_text = " ".join(topics)
    if "woodchips" in topics:
        queries.extend(_paired(
            f"{geography} woodchip plantation harvest export port supply{period}",
            f"{geography} 木片 人工林 采伐 出口 港口 供应{period}",
            "Assess plantation, harvest, logistics, and exportable woodchip supply.",
            "评估人工林、采伐、物流与木片可出口供应。",
            SourceCategory.INDUSTRY, plan.research_questions[-1].question, 1,
        ))
    if "market pulp" in topics:
        queries.extend(_paired(
            f"global hardwood pulp BHKP BEKP price inventory operating rate{period}",
            f"全球 阔叶浆 BHKP BEKP 价格 库存 开工率{period}",
            "Track pulp benchmarks, inventories, downtime, and price drivers.",
            "跟踪纸浆基准价、库存、停机及价格驱动。",
            SourceCategory.INDUSTRY, plan.research_questions[-1].question, 1,
        ))
    if "packaging paper and board" in topics:
        queries.extend(_paired(
            f"{geography} packaging board competitor mill assets capacity announcement{period}",
            f"{geography} 包装纸 白卡纸 竞争者 工厂 产能 项目公告{period}",
            "Identify competitor assets, product mix, and project announcements.",
            "识别竞争者资产、产品组合及项目公告。",
            SourceCategory.COMPANY, plan.research_questions[-1].question, 1,
        ))
    queries.extend(_paired(
        f"{geography} {topic_text} company annual report capacity cost price{period}",
        f"{geography} {request.value_chain_segment or request.research_question} 企业 年报 产能 成本 价格{period}",
        "Locate company disclosures on assets, costs, prices, and projects.",
        "查找企业对资产、成本、价格及项目的正式披露。",
        SourceCategory.COMPANY, primary_question, 3,
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
