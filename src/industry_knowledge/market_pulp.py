"""Baseline market-pulp knowledge pack."""

from src.industry_knowledge.models import IndicatorGuide, KnowledgePack, QueryTemplate

MARKET_PULP = KnowledgePack(
    "market_pulp", "Market and chemical pulp", "商品浆与化学浆",
    ("market pulp", "chemical pulp", "hardwood pulp", "softwood pulp", "BHKP", "BEKP", "NBSK", "商品浆", "化学浆", "阔叶浆", "针叶浆"),
    ("wood fiber", "woodchips", "chemicals", "energy"), ("paper and board", "tissue"),
    ("Fiber supply", "Pulp mill", "Market pulp shipment", "Customer inventory", "Paper mill"),
    ("effective capacity", "downtime and ramp-up", "producer inventory", "trade", "cash cost", "benchmark price", "downstream demand"),
    (IndicatorGuide("Capacity, production, and downtime", "air-dry tonnes/year; days", "Measure effective supply"), IndicatorGuide("Producer and customer inventory", "tonnes; days", "Track cycle pressure"), IndicatorGuide("Benchmark and net prices", "USD/air-dry tonne", "Compare grade and regional pricing")),
    ("benchmark list price", "net transaction price", "CIF price", "cash cost", "delivered fiber cost"),
    ("company disclosures", "industry price sources", "customs", "statistics"),
    ("market-pulp producers", "integrated producers", "traders", "paper and tissue buyers"),
    ("pulp mills", "ports", "warehouses"),
    ("capacity and downtime → supply", "inventory and demand → price", "fiber, chemicals, energy, and freight → cash cost"),
    ("supply-demand balance", "cost curve", "inventory-price cycle", "grade substitution"),
    (QueryTemplate("English", "global", "market pulp cycle", "global {topic} capacity downtime inventory benchmark price demand", "Assess supply, inventory, price, and demand cycle.", "Industry and professional research", 1), QueryTemplate("Chinese", "demand", "market pulp projects", "{demand_zh} 化学浆 新增产能 项目 投产 爬坡 原料需求", "评估新增产能、投产爬坡及原料需求。", "Company and regulatory disclosure", 1)),
    ("Effective supply depends on downtime and ramp-up, not nameplate capacity alone.",),
    ("List and net prices differ.", "Producer inventory definitions vary."),
    ("effective operating rate", "downtime", "demand growth", "inventory", "cash cost", "FX"),
    {"Procurement": ("supplier position", "contract exposure", "grade alternatives", "inventory triggers"), "Investment": ("cost position", "ramp-up", "cycle downside")},
)
