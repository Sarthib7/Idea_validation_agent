"""Similarweb traffic and competitor signal tool."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx
from crewai.tools import tool

from .common import dig_first, error_response, json_response, missing_config_response, normalize_domain

logger = logging.getLogger(__name__)


@tool("Similarweb Competitor Analyzer")
def similarweb_competitor_tool(website_or_domain: str, competitor_domains: str = "") -> str:
    """
    Retrieve Similarweb ranking signals for a startup website and optional competitors.

    Args:
        website_or_domain: Primary website URL or bare domain
        competitor_domains: Optional comma-separated competitor domains

    Returns:
        JSON string with rank-based competitor signals
    """
    api_key = os.getenv("SIMILARWEB_API_KEY")
    if not api_key:
        return missing_config_response(
            tool_name="Similarweb Competitor Analyzer",
            env_vars=["SIMILARWEB_API_KEY"],
            note="Traffic and rank-based competitor benchmarking will be skipped.",
        )

    primary_domain = normalize_domain(website_or_domain)
    if not primary_domain:
        return error_response("Similarweb Competitor Analyzer", "A website URL or domain is required")

    domains = [primary_domain]
    domains.extend(
        domain
        for domain in (
            normalize_domain(part)
            for part in (competitor_domains or "").split(",")
        )
        if domain and domain not in domains
    )
    domains = domains[:4]

    summaries: List[Dict[str, Any]] = []
    sources: List[Dict[str, str]] = []
    for domain in domains:
        summary = _fetch_domain_summary(domain=domain, api_key=api_key)
        summaries.append(summary)
        if summary.get("status") == "success":
            insight_parts = []
            if summary.get("global_rank") not in (None, ""):
                insight_parts.append(f"global rank {summary['global_rank']}")
            if summary.get("industry_rank") not in (None, ""):
                insight_parts.append(f"industry rank {summary['industry_rank']}")
            sources.append(
                {
                    "source_type": "similarweb",
                    "title": f"Similarweb profile for {domain}",
                    "url": f"https://www.similarweb.com/website/{domain}/",
                    "insight": ", ".join(insight_parts) or "Traffic benchmark available",
                }
            )

    return json_response(
        {
            "provider": "similarweb",
            "primary_domain": primary_domain,
            "domains_analyzed": summaries,
            "competitive_positioning": _classify_positioning(summaries),
            "sources": sources,
        }
    )


def _fetch_domain_summary(domain: str, api_key: str) -> Dict[str, Any]:
    headers = {"api-key": api_key}

    try:
        global_rank = _get_similarweb_json(
            f"https://api.similarweb.com/v1/website/{domain}/global-rank/global-rank",
            headers=headers,
        )
        category_rank = _get_similarweb_json(
            f"https://api.similarweb.com/v1/website/{domain}/category-rank/category-rank",
            headers=headers,
        )
    except httpx.HTTPError as exc:
        logger.warning("Similarweb lookup failed for %s: %s", domain, exc)
        return {
            "domain": domain,
            "status": "failed",
            "error": str(exc),
        }

    return {
        "domain": domain,
        "status": "success",
        "global_rank": _coerce_rank(
            dig_first(
            global_rank,
            ("global_rank",),
            ("rank",),
            ("global_rank", "rank"),
            ("visits", "global_rank"),
        )),
        "industry_rank": _coerce_rank(
            dig_first(
            category_rank,
            ("category_rank",),
            ("rank",),
            ("category_rank", "rank"),
        )),
        "industry": dig_first(
            category_rank,
            ("category",),
            ("category_name",),
            ("category_rank", "category"),
            ("metadata", "category"),
        ),
        "global_rank_snapshot": _compact_payload(global_rank),
        "category_rank_snapshot": _compact_payload(category_rank),
    }


def _get_similarweb_json(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    response = httpx.get(
        url,
        params={"format": "json"},
        headers=headers,
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return payload
    return {"raw": payload}


def _compact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key in {"global_rank", "category_rank", "category", "country", "rank", "metadata"}
    } or payload


def _classify_positioning(summaries: List[Dict[str, Any]]) -> str:
    successful = [summary for summary in summaries if summary.get("status") == "success"]
    if not successful:
        return "INSUFFICIENT_DATA"

    primary = successful[0]
    rank = primary.get("global_rank")
    if isinstance(rank, int):
        if rank <= 100000:
            return "STRONG_TRAFFIC_SIGNAL"
        if rank <= 1000000:
            return "MID_MARKET_SIGNAL"
        return "EARLY_OR_LOW_TRAFFIC_SIGNAL"
    return "QUALITATIVE_SIGNAL_ONLY"


def _coerce_rank(value: Any) -> Any:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()
        if cleaned.isdigit():
            return int(cleaned)
    return value
