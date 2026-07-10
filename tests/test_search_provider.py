"""Tests for provider normalization, tiering, and error handling."""

import pytest

from src.search_provider import (
    SearchProviderError, SearchResult, TavilySearchProvider, classify_source,
    deduplicate_results, normalize_url,
)
from src.search_strategy import SearchQuery, SourceCategory


QUERY = SearchQuery("test query", "test", "English", 1, SourceCategory.GOVERNMENT, "What changed?")


def _result(url: str, rank: int = 1) -> SearchResult:
    return SearchResult("Title", url, "example.com", None, "Snippet", "query",
        SourceCategory.NEWS, "Question", rank, "2026-01-01T00:00:00+00:00", 3, "General source")


def test_url_normalization_and_deduplication() -> None:
    first = "HTTPS://www.Example.com/report/?utm_source=x&a=1#part"
    second = "https://example.com/report?a=1"
    assert normalize_url(first) == "https://example.com/report?a=1"
    assert len(deduplicate_results([_result(first), _result(second, 2)])) == 1


def test_preliminary_source_tier_classification() -> None:
    tier, rationale = classify_source("stats.gov.cn")
    assert tier == 1
    assert "still require verification" in rationale
    assert classify_source("reuters.com")[0] == 2
    assert classify_source("reddit.com")[0] == 4


def test_missing_tavily_key_is_explicit(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    provider = TavilySearchProvider()
    assert not provider.configured
    with pytest.raises(SearchProviderError, match="not configured"):
        provider.search(QUERY)


def test_tavily_timeout_is_wrapped() -> None:
    class TimeoutClient:
        def search(self, **kwargs):
            raise TimeoutError("timed out")

    with pytest.raises(SearchProviderError, match="timed out"):
        TavilySearchProvider("test-key", TimeoutClient()).search(QUERY)


def test_mocked_tavily_result_is_normalized() -> None:
    class MockClient:
        def search(self, **kwargs):
            return {"results": [{"title": "Statistics", "url": "https://stats.gov.cn/data/?utm_source=x", "content": "Official data", "published_date": "2025-01-01"}]}

    results = TavilySearchProvider("test-key", MockClient()).search(QUERY)
    assert results[0].url == "https://stats.gov.cn/data"
    assert results[0].source_domain == "stats.gov.cn"
    assert results[0].source_tier == 1
