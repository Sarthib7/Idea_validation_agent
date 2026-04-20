"""News intelligence research tool."""

from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx
from crewai.tools import tool

from .common import clip_text, error_response, json_response, missing_config_response

logger = logging.getLogger(__name__)


@tool("News Intelligence")
def news_intelligence_tool(query: str, days_back: int = 90, domains: str = "") -> str:
    """
    Retrieve recent media coverage for a market, startup category, or competitor set.

    Args:
        query: Search query describing the startup category or problem space
        days_back: Number of trailing days to search (max 365)
        domains: Optional comma-separated domains to prioritize

    Returns:
        JSON string with coverage signals and source references
    """
    api_key = os.getenv("NEWSAPI_API_KEY")
    if not api_key:
        return missing_config_response(
            tool_name="News Intelligence",
            env_vars=["NEWSAPI_API_KEY"],
            note="Media coverage analysis will be skipped until NewsAPI is configured.",
        )

    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return error_response("News Intelligence", "A non-empty query is required")

    try:
        window_days = max(1, min(int(days_back or 90), 365))
    except (TypeError, ValueError):
        window_days = 90
    from_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")

    params = {
        "q": cleaned_query[:500],
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "from": from_date,
    }
    if domains.strip():
        params["domains"] = ",".join(
            part.strip() for part in domains.split(",") if part.strip()
        )

    headers = {"X-Api-Key": api_key}

    try:
        logger.info("Fetching NewsAPI coverage for query: %s", cleaned_query)
        response = httpx.get(
            "https://newsapi.org/v2/everything",
            params=params,
            headers=headers,
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        logger.error("NewsAPI request failed: %s", exc)
        return error_response("News Intelligence", str(exc), query=cleaned_query)

    if payload.get("status") != "ok":
        return error_response(
            "News Intelligence",
            payload.get("message", "NewsAPI returned a non-ok response"),
            code=payload.get("code"),
            query=cleaned_query,
        )

    articles = payload.get("articles", []) or []
    total_results = int(payload.get("totalResults") or len(articles))
    source_counts = Counter(
        article.get("source", {}).get("name", "Unknown source")
        for article in articles
        if isinstance(article, dict)
    )

    notable_articles = []
    sources = []
    for article in articles[:6]:
        title = article.get("title") or "Untitled article"
        url = article.get("url") or ""
        source_name = article.get("source", {}).get("name") or "Unknown source"
        published_at = article.get("publishedAt") or ""
        summary = clip_text(article.get("description") or article.get("content") or "", 240)

        notable_articles.append(
            {
                "title": title,
                "source": source_name,
                "published_at": published_at,
                "url": url,
                "summary": summary,
            }
        )
        sources.append(
            {
                "source_type": "newsapi",
                "title": title,
                "url": url,
                "insight": f"{source_name} coverage on {published_at[:10] or 'recent date'}",
            }
        )

    return json_response(
        {
            "query": cleaned_query,
            "provider": "newsapi",
            "coverage_window_days": window_days,
            "articles_found": total_results,
            "momentum_assessment": _assess_news_momentum(total_results),
            "source_mix": [
                {"source": source, "article_count": count}
                for source, count in source_counts.most_common(5)
            ],
            "notable_articles": notable_articles,
            "sources": sources,
        }
    )


def _assess_news_momentum(total_results: int) -> str:
    if total_results >= 50:
        return "HIGH"
    if total_results >= 15:
        return "MEDIUM"
    if total_results > 0:
        return "LOW"
    return "NONE"
