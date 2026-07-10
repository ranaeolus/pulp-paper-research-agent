# Pulp & Paper Industry Research Agent — Version 0.2

Version 0.2 adds the first functional module: an offline Research Planner for pulp and
paper industry questions. It converts a question and optional scope into a structured,
professional plan describing how the topic should be researched.

## Current capabilities

- Streamlit homepage and Research Planner form
- Deterministic topic detection across major pulp and paper value-chain segments
- Typed research requests, sub-questions, data requirements, and research plans
- Ten-section plans covering scope, hypotheses, data, sources, frameworks, and gaps
- Environment-based configuration
- Application logging
- SQLite schema initialization
- Automated tests with pytest

The local planner uses declared keyword rules and topic-specific templates. It works
without network access or an API key and produces the same output for the same input.

Version 0.2 intentionally does **not** answer the research question. It does not perform
web search, call an LLM, read PDFs, validate evidence, generate a final report, or make
investment recommendations. A future LLM planner interface exists, but its implementation
deliberately raises `NotImplementedError` and is not used by the application.

## Requirements

- Python 3.12 (supported production version; recorded in `.python-version`)
- Git

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

To run the test suite, install the development requirements instead:

```bash
pip install -r requirements-dev.txt
```

The API-key entries in `.env.example` are reserved placeholders. API integrations are
not implemented and no API keys are required for Version 0.2. Never commit `.env`.

## Run the application

```bash
streamlit run app.py
```

The application initializes `data/research_agent.db` and writes rotating logs to
`logs/research_agent.log` by default.

Open the **Research Planner** tab, enter a required research question and any optional
scope, choose the desired depth, and select **Generate Research Plan**.

## Run tests

```bash
pytest
```

## Project structure

```text
.
├── .env.example             # Safe environment-variable template
├── .gitignore               # Local, generated, and secret files excluded from Git
├── .python-version          # Supported production Python version
├── .streamlit/config.toml   # Streamlit theme and server settings
├── app.py                   # Streamlit entry point and Version 0.1 homepage
├── data/                    # Runtime SQLite database location
├── logs/                    # Runtime application logs
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Runtime and test dependencies
├── src/
│   ├── __init__.py          # Package metadata
│   ├── config.py            # Typed environment configuration
│   ├── database.py          # Idempotent SQLite schema initialization
│   ├── logging_config.py    # Console and rotating-file logging setup
│   └── research_planner.py  # Typed deterministic planning logic
└── tests/
    ├── test_app.py          # Application import test
    ├── test_config.py       # Configuration default tests
    ├── test_database.py     # Database initialization test
    ├── test_logging.py      # Logging initialization tests
    └── test_research_planner.py # Planner behavior and structure tests
```

## Research Planner example

Sample input:

```text
Research question: How will Vietnam woodchip export supply evolve?
Geographic scope: Vietnam and key Asian destinations
Product segment: Plantation woodchips
Time horizon: 2025-2030
Decision context: Procurement
Desired depth: Standard research
```

Abbreviated output:

```text
1. Restated research objective
   Develop an evidence-based approach to evaluate Vietnam woodchip export supply.
2. Scope and boundaries
   Vietnam and key Asian destinations; 2025-2030; separate actuals and forecasts.
4. Key hypotheses to test
   Export availability may be constrained by harvest economics, plantation maturity,
   domestic demand, and port logistics.
6. Required data and indicators
   Plantation area, harvest cycle, yield, domestic use, exports, and port throughput,
   with units and geographic/time dimensions stated explicitly.
```

## Current limitations

- Topic recognition is keyword-based and currently English-first.
- Plans are structured baselines, not substitutes for expert scoping on complex mandates.
- The planner does not retrieve evidence or verify whether required data is available.
- No plan history or user-submitted research content is stored in Version 0.2.

## Architecture principles

- Keep UI, configuration, persistence, and future domain logic separate.
- Read deployment-specific values from environment variables.
- Make infrastructure initialization idempotent.
- Avoid API calls and other external side effects during module import.
- Add tests alongside each module as the platform grows.
