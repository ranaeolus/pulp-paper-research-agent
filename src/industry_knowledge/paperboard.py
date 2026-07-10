"""Baseline packaging-paper and board knowledge pack."""

from src.industry_knowledge.models import IndicatorGuide, KnowledgePack, QueryTemplate

PAPERBOARD = KnowledgePack(
    "paperboard", "Packaging paper and board", "包装纸与纸板",
    ("packaging board", "containerboard", "cartonboard", "white cardboard", "FBB", "SBS", "CUK", "包装纸", "箱板纸", "瓦楞纸", "白卡纸", "白纸板"),
    ("market pulp", "recovered paper", "chemicals", "energy"), ("converting", "packaging end markets"),
    ("Fiber", "Board mill", "Converter", "Brand owner", "End market"),
    ("capacity and operating rate", "grade mix", "demand by end use", "cost and margin", "inventory", "competitor assets"),
    (IndicatorGuide("Capacity and production by grade", "tonnes/year", "Measure effective supply"), IndicatorGuide("Price, fiber cost, and gross margin", "currency/tonne; %", "Assess profitability")),
    ("ex-mill price", "delivered price", "net realized price", "gross margin"),
    ("company disclosures", "statistics", "industry publications"),
    ("board producers", "integrated groups", "converters", "brand owners"), ("board mills", "converting plants", "warehouses"),
    ("capacity and utilization → supply", "end-use demand and inventory → price", "fiber and energy → margin"),
    ("competitor benchmarking", "supply-demand balance", "margin bridge", "end-use demand tree"),
    (QueryTemplate("English", "demand", "paperboard capacity and profitability", "{demand} white cardboard FBB capacity production demand price margin company", "Assess capacity, demand, price, and competitor profitability.", "Company and regulatory disclosure", 1), QueryTemplate("Chinese", "demand", "paperboard supply demand", "{demand_zh} 白卡纸 产能 产量 需求 开工率 库存 价格", "评估白卡纸供需与价格驱动。", "Industry and professional research", 1)),
    ("Profitability depends on utilization, product mix, fiber cost, energy, and realized price.",),
    ("Capacity may include converted or idle machines.", "Margin definitions differ by company."),
    ("capacity ramp-up", "operating rate", "end-use demand", "fiber cost", "price", "inventory"),
    {"Competitive intelligence": ("asset map", "grade mix", "customers", "cost position", "announced moves"), "Investment": ("cycle margin", "utilization", "cost advantage")},
)
