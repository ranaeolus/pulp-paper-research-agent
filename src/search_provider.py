"""Provider-neutral web source discovery and Tavily integration."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.search_strategy import SearchQuery, SourceCategory


class SearchProviderError(RuntimeError):
    """A recoverable external search-provider failure."""


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    source_domain: str
    detected_date: str | None
    snippet: str
    originating_query: str
    expected_source_category: SourceCategory
    related_sub_question: str
    search_rank: int
    retrieval_timestamp: str
    source_tier: int
    classification_rationale: str
    domain_result_count: int = 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class SearchProvider(Protocol):
    def search(self, query: SearchQuery, max_results: int) -> list[SearchResult]: ...


TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalize_url(url: str) -> str:
    """Normalize a URL for display and deterministic duplicate detection."""
    raw = url.strip()
    if not raw:
        return ""
    parts = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parts.hostname or "").casefold()
    if host.startswith("www."):
        host = host[4:]
    port = parts.port
    netloc = host if port is None or (parts.scheme == "https" and port == 443) else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    query = urlencode(sorted(
        (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in TRACKING_PARAMETERS
    ))
    return urlunsplit(((parts.scheme or "https").casefold(), netloc, path, query, ""))


def classify_source(domain: str, url: str = "") -> tuple[int, str]:
    """Assign a preliminary source tier with an explicit, cautious rationale."""
    host = domain.casefold().removeprefix("www.")
    primary = (".gov", "gov.cn", "gov.vn", "fao.org", "worldbank.org", "un.org", "oecd.org", "sec.gov", "hkexnews.hk")
    professional = ("reuters.com", "bloomberg.com", "fastmarkets.com", "risiinfo.com", "spglobal.com", "mckinsey.com", "deloitte.com")
    unverified = ("reddit.com", "facebook.com", "x.com", "twitter.com", "weibo.com", "forum")
    if any(token in host for token in unverified):
        return 4, "Forum, social-media, or unattributed content; treat only as an unverified lead."
    if any(host == token or host.endswith(f".{token}") or token in host for token in primary):
        return 1, "Domain indicates a government, multilateral, exchange, or regulatory source; individual claims still require verification."
    if any(host == token or host.endswith(f".{token}") for token in professional):
        return 2, "Established professional research or business publication; methodology and cited evidence still require review."
    if any(term in url.casefold() for term in ("annual-report", "investor", "filing", "disclosure")):
        return 1, "URL appears to be an official disclosure; confirm publisher identity and document authenticity."
    return 3, "General web or trade source without sufficient signals for a higher preliminary tier."


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """Remove normalized URL duplicates while retaining domain diversity metadata."""
    seen: set[str] = set()
    unique: list[SearchResult] = []
    domain_counts: dict[str, int] = {}
    for result in results:
        normalized = normalize_url(result.url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(replace(result, url=normalized))
        domain_counts[result.source_domain] = domain_counts.get(result.source_domain, 0) + 1
    return [
        replace(result, domain_result_count=domain_counts[result.source_domain])
        for result in unique
    ]


class TavilySearchProvider:
    """Tavily adapter returning only provider-neutral normalized results."""

    def __init__(self, api_key: str | None = None, client: Any | None = None) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: SearchQuery, max_results: int = 5) -> list[SearchResult]:
        if not self.configured:
            raise SearchProviderError("TAVILY_API_KEY is not configured. Planner-only mode remains available.")
        try:
            client = self._client
            if client is None:
                from tavily import TavilyClient
                client = TavilyClient(api_key=self.api_key)
            response = client.search(
                query=query.query_text, search_depth="advanced",
                max_results=max(1, min(max_results, 20)), include_answer=False,
            )
        except Exception as error:
            raise SearchProviderError(f"Tavily search failed: {error}") from error
        timestamp = datetime.now(timezone.utc).isoformat()
        normalized: list[SearchResult] = []
        for rank, item in enumerate(response.get("results", []), start=1):
            url = normalize_url(str(item.get("url", "")))
            if not url:
                continue
            domain = urlsplit(url).hostname or ""
            tier, rationale = classify_source(domain, url)
            normalized.append(SearchResult(
                title=str(item.get("title") or "Untitled source"), url=url,
                source_domain=domain, detected_date=item.get("published_date"),
                snippet=str(item.get("content") or item.get("snippet") or ""),
                originating_query=query.query_text,
                expected_source_category=query.expected_source_type,
                related_sub_question=query.related_sub_question, search_rank=rank,
                retrieval_timestamp=timestamp, source_tier=tier,
                classification_rationale=rationale,
            ))
        return deduplicate_results(normalized)


def discover_sources(
    provider: SearchProvider, queries: tuple[SearchQuery, ...],
    max_queries: int = 8, max_results_per_query: int = 5,
) -> list[SearchResult]:
    """Run a bounded strategy and deduplicate results across all queries."""
    collected: list[SearchResult] = []
    for query in sorted(queries, key=lambda item: item.priority)[:max_queries]:
        collected.extend(provider.search(query, max_results_per_query))
    return deduplicate_results(collected)
