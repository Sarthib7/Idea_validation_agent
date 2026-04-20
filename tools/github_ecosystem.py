"""GitHub ecosystem research tool."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from crewai.tools import tool

from .common import clip_text, error_response, json_response

logger = logging.getLogger(__name__)


@tool("GitHub Ecosystem Analyzer")
def github_ecosystem_tool(query: str, language: str = "") -> str:
    """
    Search GitHub repositories to measure developer and open-source ecosystem activity.

    Args:
        query: Query representing the technology category or problem space
        language: Optional programming language qualifier

    Returns:
        JSON string containing repository intelligence and ecosystem signals
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return error_response("GitHub Ecosystem Analyzer", "A non-empty query is required")

    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    search_query = f"{cleaned_query} in:name,description,readme"
    if language.strip():
        search_query += f" language:{language.strip()}"

    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": 8,
    }

    try:
        logger.info("Searching GitHub ecosystem for: %s", search_query)
        response = httpx.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        logger.error("GitHub search failed: %s", exc)
        return error_response("GitHub Ecosystem Analyzer", str(exc), query=search_query)

    repositories = payload.get("items", []) or []
    total_count = int(payload.get("total_count") or len(repositories))
    active_cutoff = datetime.now(timezone.utc) - timedelta(days=180)

    repo_summaries = []
    source_register = []
    total_stars = 0
    active_repo_count = 0

    for repository in repositories[:6]:
        stars = int(repository.get("stargazers_count") or 0)
        total_stars += stars
        updated_at = repository.get("updated_at") or ""
        if updated_at:
            try:
                updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if updated_dt >= active_cutoff:
                    active_repo_count += 1
            except ValueError:
                pass

        repo_entry = {
            "full_name": repository.get("full_name"),
            "description": clip_text(repository.get("description") or "", 180),
            "stars": stars,
            "forks": int(repository.get("forks_count") or 0),
            "open_issues": int(repository.get("open_issues_count") or 0),
            "language": repository.get("language"),
            "topics": repository.get("topics") or [],
            "updated_at": updated_at,
            "url": repository.get("html_url"),
        }
        repo_summaries.append(repo_entry)
        source_register.append(
            {
                "source_type": "github",
                "title": repo_entry.get("full_name") or "GitHub repository",
                "url": repo_entry.get("url") or "",
                "insight": f"{stars} stars; updated {updated_at[:10] or 'recently'}",
            }
        )

    return json_response(
        {
            "query": cleaned_query,
            "provider": "github",
            "authenticated": bool(token),
            "repositories_found": total_count,
            "recently_active_repositories": active_repo_count,
            "aggregate_top_repo_stars": total_stars,
            "ecosystem_signal": _classify_ecosystem_signal(total_count, total_stars, active_repo_count),
            "top_repositories": repo_summaries,
            "sources": source_register,
        }
    )


def _classify_ecosystem_signal(total_count: int, total_stars: int, active_repo_count: int) -> str:
    if total_count >= 100 and total_stars >= 10000 and active_repo_count >= 3:
        return "STRONG"
    if total_count >= 20 and total_stars >= 1000:
        return "EMERGING"
    if total_count > 0:
        return "NICHE"
    return "LIMITED"
