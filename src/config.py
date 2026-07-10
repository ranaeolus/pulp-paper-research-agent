"""Environment-based application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # Allows infrastructure tooling before dependencies are installed.
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings for the application foundation."""

    app_name: str = "Pulp & Paper Industry Research Agent"
    app_version: str = "0.2"
    app_env: str = "development"
    log_level: str = "INFO"
    database_path: Path = PROJECT_ROOT / "data" / "research_agent.db"
    log_path: Path = PROJECT_ROOT / "logs" / "research_agent.log"


def _project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process from `.env` and the environment."""
    if load_dotenv is not None:
        load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        database_path=_project_path(
            os.getenv("DATABASE_PATH", "data/research_agent.db")
        ),
    )
