"""Centralized application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src.config import Settings

LOGGER_NAME = "pulp_paper_research_agent"


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure and return the application logger without duplicate handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    level = getattr(logging, settings.log_level, logging.INFO)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    settings.log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        settings.log_path,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
