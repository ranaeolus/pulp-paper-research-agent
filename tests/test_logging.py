"""Tests for logging infrastructure."""

import logging
from pathlib import Path

from src.config import Settings
from src.logging_config import LOGGER_NAME, configure_logging


def test_logging_initializes_without_duplicate_handlers(tmp_path: Path) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    log_path = tmp_path / "application.log"
    settings = Settings(log_path=log_path)

    first_logger = configure_logging(settings)
    second_logger = configure_logging(settings)
    first_logger.info("logging test marker")

    assert first_logger is second_logger
    assert len(first_logger.handlers) == 2
    assert log_path.exists()
    assert "logging test marker" in log_path.read_text(encoding="utf-8")

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
