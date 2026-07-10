"""Smoke tests for the application entry point."""

import importlib


def test_app_imports_successfully() -> None:
    module = importlib.import_module("app")

    assert callable(module.main)
