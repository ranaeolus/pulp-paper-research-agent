"""Typed, deterministic research planning for the pulp and paper value chain."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from itertools import zip_longest
from typing import Protocol

from src.industry_knowledge.models import IndustryInterpretation
from src.industry_knowledge.registry import get_knowledge_pack, interpret_request


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    """User inputs that define a research-planning task."""

    research_question: str
    geographic_scope: str = ""
    value_chain_segment: str = ""
    time_horizon: str = ""
    decision_context: str = ""
    desired_depth: str = "Standard research"
    output_language: str = "English"

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
class ResearchScenario:
    name: str
    assumptions: tuple[str, ...]
    key_variables: tuple[str, ...]
    triggers: tuple[str, ...]
    evidence_required: tuple[str, ...]
    decision_implications: tuple[str, ...]


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
    scenario_structure: tuple[ResearchScenario, ...]
    risks_and_data_gaps: tuple[str, ...]
    proposed_deliverable_structure: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a stable serialization suitable for UI or persistence."""
        return asdict(self)


class ResearchPlanner(Protocol):
    """Interface implemented by local and future LLM-backed planners."""

    def generate_plan(self, request: ResearchRequest, interpretation: IndustryInterpretation | None = None) -> ResearchPlan:
        """Create a research plan without answering the research question."""


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "forestry and plantations": ("forest", "forestry", "plantation", "eucalyptus", "acacia", "林业", "人工林", "林地", "桉木", "相思木"),
    "woodchips": ("woodchip", "wood chip", "chips", "木片", "制浆木片"),
    "recovered paper": ("recovered paper", "waste paper", "occ", "rccm", "rcp", "废纸", "回收纸"),
    "market pulp": ("market pulp", "hardwood pulp", "softwood pulp", "bskp", "bhkp", "nbsk", "bekp", "pulp price", "商品浆", "针叶浆", "阔叶浆", "本色浆", "化机浆", "溶解浆"),
    "integrated pulp and paper": ("integrated pulp", "integrated mill", "pulp and paper mill", "浆纸一体化"),
    "packaging paper and board": ("packaging", "containerboard", "packaging board", "cartonboard", "linerboard", "boxboard", "sbs", "fbb", "cuk", "包装纸", "箱板纸", "瓦楞纸", "白卡纸", "白纸板"),
    "printing and writing paper": ("printing paper", "writing paper", "uncoated freesheet", "coated paper", "文化纸"),
    "tissue": ("tissue", "toilet paper", "facial tissue", "生活用纸"),
    "specialty paper": ("specialty paper", "speciality paper", "thermal paper", "release liner", "特种纸"),
    "pulp and paper chemicals": ("paper chemicals", "pulp chemicals", "caustic soda", "starch", "latex", "造纸化学品"),
    "biomass and energy": ("biomass", "energy", "power", "black liquor", "recovery boiler", "生物质能源"),
    "logistics, ports, and shipping": ("logistics", "port", "shipping", "freight", "vessel", "海运", "港口"),
    "trade flows": ("trade", "export", "import", "shipment", "customs", "贸易流", "出口", "进口"),
    "capacity additions and shutdowns": ("capacity", "new mill", "addition", "shutdown", "closure", "conversion", "新增产能", "停机检修", "关停"),
    "costs, margins, inventories, and prices": ("cost", "margin", "inventory", "inventories", "price", "profitability", "库存", "成本", "毛利", "价格"),
}

TOPIC_LABEL_ZH = {
    "forestry and plantations": "林业与人工林", "woodchips": "木片",
    "recovered paper": "废纸与回收纸", "market pulp": "商品浆",
    "integrated pulp and paper": "浆纸一体化", "packaging paper and board": "包装纸与纸板",
    "printing and writing paper": "文化纸", "tissue": "生活用纸", "specialty paper": "特种纸",
    "pulp and paper chemicals": "制浆造纸化学品", "biomass and energy": "生物质与能源",
    "logistics, ports, and shipping": "物流、港口与海运", "trade flows": "贸易流",
    "capacity additions and shutdowns": "新增产能与停机退出",
    "costs, margins, inventories, and prices": "成本、毛利、库存与价格",
    "general pulp and paper market": "一般制浆造纸市场",
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

    def generate_plan(self, request: ResearchRequest, interpretation: IndustryInterpretation | None = None) -> ResearchPlan:
        interpretation = interpretation or interpret_request(request)
        if request.output_language == "Chinese":
            plan = self._generate_chinese(request)
        elif request.output_language == "Bilingual":
            english = self._generate_english(replace(request, output_language="English"))
            chinese = self._generate_chinese(replace(request, output_language="Chinese"))
            plan = self._combine_bilingual(chinese, english)
        else:
            plan = self._generate_english(request)
        return self._apply_industry_guidance(plan, request, interpretation)

    def _generate_english(self, request: ResearchRequest) -> ResearchPlan:
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
            scenario_structure=(),
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

    def _generate_chinese(self, request: ResearchRequest) -> ResearchPlan:
        topics = detect_topics(request)
        geography = request.geographic_scope.strip() or "问题所涉及的地区"
        geography = {"Vietnam and China": "越南与中国", "China": "中国", "Vietnam": "越南", "Global": "全球"}.get(geography, geography)
        horizon = request.time_horizon.strip() or "最新可得历史数据及明确标注的前瞻期"
        segment = request.value_chain_segment.strip() or "、".join(TOPIC_LABEL_ZH[topic] for topic in topics)
        context = {
            "Market intelligence": "市场情报", "Strategy": "战略", "Investment": "投资",
            "Supply chain": "供应链", "Procurement": "采购",
            "Competitive intelligence": "竞争情报", "Executive briefing": "管理层简报",
        }.get(request.decision_context.strip(), request.decision_context.strip()) or "一般市场研判"
        depth = {
            "Rapid scan": "快速扫描", "Standard research": "标准研究", "Deep research": "深度研究",
        }.get(request.desired_depth, request.desired_depth)
        hypotheses = [
            f"{geography}的供应可得性可能受到产能、开工率及运营约束的实质影响。",
            "市场变化需要分别检验供应、需求、贸易、成本、库存、价格与政策变量，不能归因于单一因素。",
        ]
        questions = [
            ResearchSubQuestion("当前及历史供需平衡如何？", ("产能", "产量", "开工率", "消费量")),
            ResearchSubQuestion("贸易流与政策如何改变区域可得量？", ("进口", "出口", "关税", "监管政策")),
            ResearchSubQuestion("哪些成本、库存与价格传导机制最重要？", ("现金成本", "运费", "库存", "基准价格")),
        ]
        data = [
            DataRequirement("产能、产量与开工率", "衡量有效供应", "吨/年；吨；%", horizon, ("国家", "企业", "工厂", "品种")),
            DataRequirement("需求与消费量", "衡量终端需求拉动", "吨；同比%", horizon, ("国家", "终端用途", "品种")),
            DataRequirement("贸易流", "核对区域可得量", "吨及注明币种的金额", horizon, ("来源地", "目的地", "海关编码")),
            DataRequirement("成本、库存与价格", "检验经济性与周期信号", "币种/吨；库存天数或吨", horizon, ("品种", "地区", "交付口径", "币种")),
        ]
        frameworks = [
            "供需平衡：明确核对产量、消费量与净贸易",
            "成本曲线与到岸成本比较：统一币种、单位及运费口径",
            "驱动因素树：区分供应、需求、贸易、成本、库存、价格与政策变量",
        ]
        definitions = [f"明确界定{TOPIC_LABEL_ZH[topic]}的纳入范围与边界。" for topic in topics]
        risks = [
            "公开数据可能在产品定义、单位、币种、统计年度或修订状态上不一致。",
            "非上市公司的产量、成本、库存及客户数据可能缺失，需要交叉验证。",
            "项目公告不等于已融资、已投产或达到有效产能。",
            "预测取决于情景假设，应标注置信度，不得作为既成事实。",
        ]
        if "woodchips" in topics:
            hypotheses.append("木片出口可得量可能受采伐经济性、林龄结构、国内需求及港口物流约束。")
            questions.append(ResearchSubQuestion("木片供应是否可持续并具备扩张空间？", ("人工林面积", "采伐周期", "单产", "国内消耗", "港口吞吐")))
            data.append(DataRequirement("人工林与木片供应", "评估可持续出口量", "公顷；立方米/公顷/年；绝干吨", horizon, ("树种", "林龄", "省份", "港口")))
            frameworks.append("生物供应桥：人工林面积 × 可采比例 × 单产 × 木片得率")
            risks.append("林龄、所有权、认证、天气及非法采伐数据可能不完整。")
        if "market pulp" in topics:
            hypotheses.append("浆价方向可能与生产商库存、开工率、停机、成本曲线及下游需求共同相关。")
            questions.append(ResearchSubQuestion("相关纸浆基准价格由哪些因素及周期驱动？", ("浆种价差", "生产商库存", "停机", "纸张需求", "汇率")))
            data.append(DataRequirement("纸浆基准价格序列", "区分浆种及区域价格影响", "币种/风干吨", horizon, ("阔叶/针叶", "价格基准", "交付条件")))
            frameworks.append("价格周期分析：联结库存、开工率、停机、浆种价差及下游需求")
        if "packaging paper and board" in topics:
            hypotheses.append("竞争优势可能取决于到岸成本、产品组合、一体化程度、客户覆盖及产能爬坡质量。")
            questions.append(ResearchSubQuestion("竞争者的定位与可能行为有何差异？", ("工厂布局", "品种结构", "一体化", "客户", "公告产能")))
            data.append(DataRequirement("竞争者资产与产品画像", "比较战略位置", "吨/年；现金成本/吨；市场份额%", horizon, ("企业", "工厂", "品种", "客户地区")))
            frameworks.append("竞争对标：资产、一体化、成本、产品组合、客户及公告项目")
        if "capacity additions and shutdowns" in topics:
            definitions.append("区分名义产能、有效产量与商业爬坡进度。")
        if "costs, margins, inventories, and prices" in topics:
            definitions.append("明确价格基准、品种、币种、交付条款、单位及名义/实际口径。")
        if "trade flows" in topics:
            definitions.append("明确海关编码、来源地/目的地、毛重/净重及数据时滞。")
            risks.append("海关编码汇总、转口贸易与报告时滞可能掩盖实际贸易流。")
        return ResearchPlan(
            restated_objective=f"制定基于证据的研究路径，评估：{request.research_question.strip()}。研究将服务于{context}，不把未经验证的假设当作结论。",
            scope_and_boundaries=(
                f"地理范围：{geography}。", f"产品/价值链范围：{segment}。",
                f"时间范围：{horizon}；分别标注历史实际值、估算值与预测值。",
                f"研究深度：{depth}；优先覆盖关键决策变量。",
                "不采用无依据的预测，并区分公告、已融资、在建及已运营产能。",
            ),
            key_definitions=tuple(definitions), hypotheses_to_test=tuple(hypotheses),
            research_questions=tuple(questions), required_data=tuple(data),
            recommended_source_hierarchy=(
                "一级：政府、海关、统计机构、监管文件、交易所披露及企业正式公告",
                "二级：行业协会一手数据、权威行业出版物及研究机构",
                "三级：主流财经媒体、专业贸易媒体及咨询机构，用于交叉验证",
                "四级：一般媒体、营销页面、博客、论坛及聚合内容，仅作为待核实线索",
            ),
            analytical_frameworks=tuple(frameworks), risks_and_data_gaps=tuple(risks),
            scenario_structure=(),
            proposed_deliverable_structure=(
                "执行摘要：已验证发现、决策含义及置信度", "范围、定义、方法、单位、币种及来源质量说明",
                "围绕核心研究问题组织的市场与价值链证据", "假设检验：支持、否定或尚未解决",
                "在证据允许时提供情景、敏感性及决策含义", "风险、数据缺口、监测指标及来源附录",
            ),
        )

    @staticmethod
    def _combine_bilingual(chinese: ResearchPlan, english: ResearchPlan) -> ResearchPlan:
        def pair(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
            return tuple(
                f"{zh}\n{en}" if zh and en else zh or en
                for zh, en in zip_longest(left, right, fillvalue="")
            )

        def pair_questions() -> tuple[ResearchSubQuestion, ...]:
            return tuple(ResearchSubQuestion(f"{zh.question}\n{en.question}", zh.variables + en.variables) for zh, en in zip(chinese.research_questions, english.research_questions))

        def pair_data() -> tuple[DataRequirement, ...]:
            return tuple(DataRequirement(f"{zh.indicator} / {en.indicator}", f"{zh.purpose} / {en.purpose}", f"{zh.unit} / {en.unit}", f"{zh.time_period} / {en.time_period}", zh.dimensions + en.dimensions) for zh, en in zip(chinese.required_data, english.required_data))

        return ResearchPlan(
            f"{chinese.restated_objective}\n{english.restated_objective}",
            pair(chinese.scope_and_boundaries, english.scope_and_boundaries),
            pair(chinese.key_definitions, english.key_definitions),
            pair(chinese.hypotheses_to_test, english.hypotheses_to_test),
            pair_questions(), pair_data(),
            pair(chinese.recommended_source_hierarchy, english.recommended_source_hierarchy),
            pair(chinese.analytical_frameworks, english.analytical_frameworks),
            (),
            pair(chinese.risks_and_data_gaps, english.risks_and_data_gaps),
            pair(chinese.proposed_deliverable_structure, english.proposed_deliverable_structure),
        )

    @staticmethod
    def _apply_industry_guidance(
        plan: ResearchPlan, request: ResearchRequest, interpretation: IndustryInterpretation
    ) -> ResearchPlan:
        pack = get_knowledge_pack(interpretation.primary_topic)
        chinese = request.output_language == "Chinese"
        bilingual = request.output_language == "Bilingual"
        def localized(zh: str, en: str) -> str:
            return zh if chinese else (f"{zh}\n{en}" if bilingual else en)

        questions = list(plan.research_questions)
        data = list(plan.required_data)
        frameworks = list(plan.analytical_frameworks)
        hypotheses = list(plan.hypotheses_to_test)
        deliverable = list(plan.proposed_deliverable_structure)
        risks = list(plan.risks_and_data_gaps)

        if interpretation.primary_topic == "woodchips":
            hypotheses.extend(localized(
                "可出口木片供应取决于可采林资源、国内消耗与物流能力，而非人工林总面积本身。",
                "Exportable chip supply depends on harvestable resource, domestic use, and logistics—not plantation area alone.",
            ) for _ in (0,))
            hypotheses.append(localized(
                "中国新增化学浆产能只有在项目投产爬坡并进入原料采购后，才会转化为木片竞争需求。",
                "New Chinese chemical-pulp capacity becomes competing woodchip demand only as projects commission, ramp up, and procure fiber.",
            ))
            questions.extend((
                ResearchSubQuestion(localized("越南人工林资源如何转化为可持续采伐量？", "How does Vietnam plantation resource translate into sustainable harvest?"), ("人工林面积", "林龄", "单产", "轮伐期", "认证") if chinese else ("plantation area", "age class", "yield", "rotation", "certification")),
                ResearchSubQuestion(localized("国内消费后有多少木片形成可竞争的出口供应？", "How much chip supply remains contestable for export after domestic use?"), ("木片产量", "国内消费", "可出口余量") if chinese else ("chip production", "domestic consumption", "exportable surplus")),
                ResearchSubQuestion(localized("港口、堆场、装船效率、船型与运费形成哪些瓶颈？", "Which port, stockyard, loading, vessel, and freight constraints limit exports?"), ("吞吐量", "装船效率", "堆存", "吃水", "运费") if chinese else ("throughput", "loading rate", "storage", "draft", "freight")),
                ResearchSubQuestion(localized("哪些现有与新增浆厂将成为竞争买家，其木片需求和采购区域如何重叠？", "Which current and future mills are competing buyers, and where do their demand and sourcing regions overlap?"), ("投产", "爬坡", "木片单耗", "自有供应", "长协供应", "港口重叠") if chinese else ("commissioning", "ramp-up", "wood intensity", "captive supply", "contracted supply", "port overlap")),
                ResearchSubQuestion(localized("FOB、CIF、海关单价与到厂成本如何形成并为何不可直接比较？", "How are FOB, CIF, customs unit value, and mill-delivered cost formed and why are they not directly comparable?"), ("FOB", "港口处理", "运费", "CIF", "汇率", "质量", "合同条款") if chinese else ("FOB", "handling", "freight", "CIF", "FX", "quality", "contract terms")),
                ResearchSubQuestion(localized("澳大利亚、泰国、马来西亚、印度尼西亚、巴西或中国国内供应能否替代？", "Can Australia, Thailand, Malaysia, Indonesia, Brazil, or domestic China substitute as supply origins?"), ("可得量", "质量", "运费", "到岸成本平价", "切换约束") if chinese else ("availability", "quality", "freight", "delivered-cost parity", "switching constraints")),
            ))
            indicator_zh = (
                ("人工林面积、林龄、单产与认证", "估算可持续可采资源"), ("采伐量与木片产量", "从生物资源推导木片产出"),
                ("国内消费与可出口余量", "区分资源量与可竞争出口供应"), ("出口量、目的地与海关单价", "衡量贸易量、金额与隐含价格"),
                ("港口能力、装船效率、堆存、船型与吃水", "检验实物出口瓶颈"), ("运费、航程与到厂成本", "核对FOB、运费、CIF及到厂成本"),
                ("浆项目产能、爬坡与木片单耗", "估算未来竞争需求"),
            )
            data.extend(DataRequirement(indicator_zh[n][0] if chinese else i.name, indicator_zh[n][1] if chinese else i.purpose, i.unit, request.time_horizon or ("明确的历史及前瞻期" if chinese else "Defined historical and forward period"), (("越南" if interpretation.supply_geography == "Vietnam" else interpretation.supply_geography), ("中国" if interpretation.demand_geography == "China" else interpretation.demand_geography))) for n, i in enumerate(pack.indicators))
            frameworks.extend(pack.frameworks)
            risks.extend(pack.data_quality_risks)
        else:
            hypotheses.extend(pack.hypotheses)
            data.extend(
                DataRequirement(
                    indicator.name, indicator.purpose, indicator.unit,
                    request.time_horizon or "Defined historical and forward period",
                    (interpretation.supply_geography, interpretation.demand_geography),
                )
                for indicator in pack.indicators
            )
            frameworks.extend(pack.frameworks)
            risks.extend(pack.data_quality_risks)

        frameworks.append(localized(
            "价值链与交易点映射：识别所有权、合同关系、实物流瓶颈、定价点、提前期、产能约束及利润分配。",
            "Value-chain and transaction-point map covering ownership, contracts, physical bottlenecks, pricing points, lead times, capacity constraints, and margin capture.",
        ))
        adaptations = pack.decision_adaptations.get(interpretation.decision_objective, ())
        if adaptations:
            procurement_zh = ("供应可得性", "竞争买家与项目地图", "可竞争供应", "港口重叠与物流瓶颈", "FOB/CIF/到厂成本形成", "合同（长协）与现货策略", "来源多元化", "谈判议价能力", "风险触发因素与监测指标")
            localized_adaptations = procurement_zh if chinese and interpretation.decision_objective == "Procurement" else adaptations
            deliverable = [localized("决策导向的执行摘要", "Decision-oriented executive summary")] + [localized(f"重点：{item}", f"Priority: {item}") for item in localized_adaptations] + deliverable

        scenarios: tuple[ResearchScenario, ...] = ()
        future_terms = ("future", "202", "未来", "新增", "价格", "supply", "demand", "供给", "需求", "竞争")
        if request.desired_depth in ("Standard research", "Deep research") and any(term in request.research_question.casefold() for term in future_terms):
            scenario_zh = ("可采人工林资源量", "国内木材需求", "可出口余量", "港口吞吐", "运费与汇率", "中国项目投产与爬坡", "木片单耗", "替代来源到岸成本", "政策与认证约束")
            common_evidence = scenario_zh if chinese else tuple(pack.scenario_variables)
            scenarios = (
                ResearchScenario(localized("基准情景", "Base case"), (localized("按已验证的项目进度与中性供应假设。", "Use verified project schedules and neutral supply assumptions."),), common_evidence, (localized("项目按计划爬坡，供应与物流无重大扰动。", "Projects ramp as scheduled with no major supply or logistics shock."),), common_evidence, (localized("据此制定基准采购量、合同组合与监测阈值。", "Set baseline procurement volumes, contract mix, and monitoring thresholds."),)),
                ResearchScenario(localized("供应偏紧/高价情景", "Tight-supply / high-price case"), (localized("可出口量下降、竞争买家需求上升或物流受限。", "Exportable supply falls, competing demand rises, or logistics tighten."),), common_evidence, (localized("采伐/天气/政策冲击、项目提前爬坡、港口拥堵或运费上涨。", "Harvest/weather/policy shock, faster ramp-up, congestion, or freight increase."),), common_evidence, (localized("提高供应保障、锁量、来源多元化与价格风险管理。", "Increase supply security, volume coverage, origin diversification, and price-risk controls."),)),
                ResearchScenario(localized("供应宽松/低价情景", "Loose-supply / low-price case"), (localized("可出口量增加、项目延期或替代来源竞争增强。", "Exportable supply rises, projects delay, or alternative origins compete."),), common_evidence, (localized("高采伐量、需求推迟、运费下降或替代来源到岸成本改善。", "Higher harvest, delayed demand, lower freight, or improved alternative-origin parity."),), common_evidence, (localized("保留现货灵活性并利用议价窗口，避免过度锁定高价。", "Preserve spot flexibility and negotiation leverage; avoid excessive high-price coverage."),)),
            )
        return replace(plan, hypotheses_to_test=tuple(hypotheses), research_questions=tuple(questions), required_data=tuple(data), analytical_frameworks=tuple(frameworks), scenario_structure=scenarios, risks_and_data_gaps=tuple(risks), proposed_deliverable_structure=tuple(deliverable))

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

    def generate_plan(self, request: ResearchRequest, interpretation: IndustryInterpretation | None = None) -> ResearchPlan:
        raise NotImplementedError("LLM-backed planning is not implemented in Version 0.3.")
