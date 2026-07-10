"""Tests for environment-based configuration."""

from pathlib import Path

import src.config as config


def test_settings_use_safe_defaults(monkeypatch) -> None:
    for variable in (
        "APP_ENV",
        "LOG_LEVEL",
        "DATABASE_PATH",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.database_path == config.PROJECT_ROOT / "data" / "research_agent.db"
    assert settings.log_path == config.PROJECT_ROOT / "logs" / "research_agent.log"
    assert isinstance(settings.database_path, Path)
    config.get_settings.cache_clear()
