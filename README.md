# Pulp & Paper Industry Research Agent — Version 0.3.1

Version 0.3.1 provides industry-aware bilingual research planning and candidate web-source discovery for
pulp and paper industry questions. It defines how a question should be researched; it
does not produce a final research conclusion.

## Capabilities

- Deterministic Chinese and English industry-term detection
- Chinese, English, or bilingual ten-section research plans
- Targeted Chinese and English search-query strategies
- Optional Tavily web discovery behind a provider-neutral interface
- Normalized URLs, duplicate removal, duplicate-domain counts, and preliminary source tiers
- SQLite persistence for requests, plans, strategies, discovery sessions, and candidates
- Fully usable offline planner mode when no API key is configured
- Semantic interpretation of primary/secondary topics, geography roles, causal chain, and decision objective
- Editable interpretation overrides that regenerate and persist the plan and strategy
- Lightweight topic knowledge packs that guide research design without asserting market facts

Version 0.3 intentionally excludes PDF processing, final report generation, claim
verification, authentication, multi-agent frameworks, monitoring, and deployment.

## Requirements and setup

- Python 3.12 (supported production version; recorded in `.python-version`)
- Git

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
cp .env.example .env
```

For runtime-only installation, use `pip install -r requirements.txt`.

## Configuration

The application works without an API key. To enable source discovery, set the Tavily
key only in the ignored `.env` file:

```text
TAVILY_API_KEY=your-key-here
MAX_SEARCH_QUERIES=8
MAX_RESULTS_PER_QUERY=5
```

Never commit `.env`. API keys are read at runtime and are never stored in SQLite.

## Run

```bash
streamlit run app.py
```

1. Open **Research Planner**.
2. Enter a Chinese or English question and optional scope.
3. Select Chinese, English, or Bilingual output; Chinese is the UI default.
4. Generate the plan.
5. Open **Source Discovery** to review the bilingual query strategy.
6. If Tavily is configured, start bounded web discovery.

Before the search strategy, the application shows its **Industry interpretation**:
primary and secondary objects, supply and demand geographies, decision objective,
value-chain relationship, causal chain, confidence, and rationale. Expand **Edit
interpretation and regenerate** to override these fields. The corrected interpretation,
plan, and query strategy are saved together.

Without `TAVILY_API_KEY`, the planner and query strategy remain available and the UI
clearly explains that discovery is disabled. No invented results are generated.

## Deploy to Render

The repository includes `render.yaml` for a Render Python web service. Render uses the
project's `.python-version` file to select Python 3.12.

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and connect this repository.
3. Review the `pulp-paper-research-agent` service and deploy it.
4. Optionally add `TAVILY_API_KEY` in the Render dashboard to enable web discovery.
5. Optionally override `MAX_SEARCH_QUERIES` and `MAX_RESULTS_PER_QUERY` there.

Render provides `PORT` automatically. The service starts with:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

Do not add API keys to `render.yaml`. They must be configured as secret environment
variables in the Render dashboard.

The current SQLite database (`data/research_agent.db`) and application log
(`logs/research_agent.log`) use the service's local filesystem. Render's default service
filesystem is ephemeral, so these files are runtime conveniences only and are **not**
relied upon as permanent storage. Deploys, restarts, or instance replacement may discard
them. Durable history will require a managed database or persistent disk in a later version.

## Source tiers

- **Tier 1 — Primary and authoritative:** government, customs, statistics agencies,
  multilaterals, exchanges, regulatory filings, and apparent official disclosures.
- **Tier 2 — Professional secondary:** established industry publications, recognized
  research organizations, and reputable financial or business media.
- **Tier 3 — Supplementary:** general media, trade sites, marketing pages, and specialist blogs.
- **Tier 4 — Unverified leads:** forums, social media, and aggregated or unattributed content.

Tiering is preliminary. A professional-looking domain does not prove that an individual
claim, number, or document is reliable. Every candidate still requires evidence review.

## Persistence

The application creates `data/research_agent.db` and `logs/research_agent.log`. SQLite
schema version 4 stores the submitted request, industry interpretation, generated plan, search strategy, discovery
session status, normalized candidates, and timestamps. Initialization is idempotent and
does not erase prior records. Runtime database and log files are ignored by Git.

## Tests

```bash
pytest
```

Tests use temporary databases and mocked Tavily clients; they make no real external API calls.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── src/
│   ├── config.py
│   ├── database.py
│   ├── logging_config.py
│   ├── industry_knowledge/
│   │   ├── models.py
│   │   ├── registry.py
│   │   ├── woodchips.py
│   │   ├── market_pulp.py
│   │   ├── paperboard.py
│   │   └── chemicals.py
│   ├── research_planner.py
│   ├── search_provider.py
│   └── search_strategy.py
└── tests/
```

## Example

Input:

```text
研究问题：越南制浆木片出口供应未来五年如何变化？
地理范围：越南及中国
时间范围：2025-2030
决策场景：采购
输出语言：中文
```

The planner produces Chinese scope definitions, hypotheses to test, sub-questions, data
requirements with units and periods, source priorities, frameworks, risks, and a proposed
deliverable structure. The search strategy separately proposes targeted Chinese and English
queries for plantation supply, harvest, exports, port logistics, company disclosures, and
official statistics.

## Industry knowledge layer

Knowledge packs are small, typed collections of research guidance. They contain terminology,
value-chain links, analytical dimensions, indicators and units, price-point definitions,
source/entity/infrastructure categories, causal mechanisms, frameworks, query templates,
hypotheses, data-quality risks, scenario variables, and decision-context adaptations.
They contain no current market numbers or unsupported conclusions.

Current packs:

- **Woodchips** — detailed resource-to-mill chain, export logistics, procurement competition,
  FOB/CIF/delivered-cost logic, alternative origins, and scenario design.
- **Market pulp** — baseline capacity, downtime, inventory, cost, price, and demand-cycle guidance.
- **Packaging paper and board** — baseline supply-demand, margin, grade, and competitor guidance.
- **Pulp and paper chemicals** — baseline application demand, technology, supplier, and competition guidance.

Topic interpretation scores declared synonyms, distinguishes primary from secondary objects,
and assigns geography roles using the wording and scope. For example, a Vietnam woodchip
supply question linked to new Chinese chemical-pulp capacity assigns Vietnam as supply/export
geography and China as demand/import geography. Confidence and rationale remain visible so
professional judgment can correct the interpretation.

To add a future pack, create one `KnowledgePack` module under `src/industry_knowledge/`,
register it in `registry.py`, and add focused deterministic tests. Keep packs as research
guidance rather than a factual market database.

## Current limitations

- Terminology detection is rule-based; ambiguous questions may need explicit segment input.
- Geography-role inference currently covers a focused set of common English and Chinese geographies.
- Knowledge packs guide scoping but do not replace analyst judgment or external evidence.
- Chinese explanatory templates cover the supported industry topics but are not machine translation.
- Tavily candidates are discovery leads, not verified evidence.
- Date availability depends on provider metadata.
- Source tiering is heuristic and preliminary.
- The system does not fetch full documents, reconcile conflicting claims, or generate conclusions.
- The LLM planner interface remains intentionally unimplemented.
