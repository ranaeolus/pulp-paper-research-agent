"""Baseline pulp-and-paper chemicals knowledge pack."""

from src.industry_knowledge.models import IndicatorGuide, KnowledgePack, QueryTemplate

CHEMICALS = KnowledgePack(
    "chemicals", "Pulp and paper chemicals", "制浆造纸化学品",
    ("paper chemicals", "pulp chemicals", "chemicals strategy", "wet strength agent", "wet-strength-agent", "wet-strength resin", "PAE", "AKD", "ASA", "造纸化学品", "化学品战略", "湿强剂", "施胶剂"),
    ("chemical feedstocks",), ("pulp", "paper", "paperboard", "tissue"),
    ("Feedstock", "Chemical producer", "Distributor", "Paper mill application"),
    ("market by chemistry", "supplier capacity", "application demand", "technology", "pricing", "competitive landscape"),
    (IndicatorGuide("Capacity and sales by chemistry", "tonnes/year; currency", "Map competitive scale"), IndicatorGuide("Application intensity", "kg/tonne of paper", "Link paper output to demand")),
    ("list price", "net price", "delivered chemical cost", "cost per tonne of paper"),
    ("company disclosures", "patents and technical literature", "chemical associations", "environmental regulation"),
    ("global chemical groups", "regional suppliers", "distributors", "paper-mill customers"), ("chemical plants", "warehouses", "application laboratories"),
    ("paper output and dosage → demand", "feedstock and regulation → cost", "performance and qualification → switching barriers"),
    ("competitive landscape", "application-demand model", "technology and qualification map", "cost-in-use comparison"),
    (QueryTemplate("English", "global", "chemicals competition", "global {topic} suppliers capacity paper application strategy annual report", "Map suppliers, technology, capacity, applications, and strategy.", "Company and regulatory disclosure", 1), QueryTemplate("Chinese", "demand", "chemicals market", "{demand_zh} {topic_zh} 供应商 产能 应用 竞争格局 价格", "研究供应商、产能、应用、竞争与价格。", "Industry and professional research", 1)),
    ("Supplier position depends on qualification, performance, service, and cost-in-use—not volume alone.",),
    ("Chemical product definitions and active-content bases vary.", "Private supplier data may be sparse."),
    ("paper output", "dosage", "feedstock cost", "qualification wins", "regulation", "capacity"),
    {"Strategy": ("portfolio fit", "regional route to market", "technology position", "partnerships"), "Competitive intelligence": ("supplier map", "applications", "capacity", "customer qualification")},
)
