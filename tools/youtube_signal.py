"""YouTube discourse research tool."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx
from crewai.tools import tool

from .common import clip_text, error_response, json_response, missing_config_response

logger = logging.getLogger(__name__)


@tool("YouTube Market Signal")
def youtube_market_signal_tool(query: str, max_results: int = 5) -> str:
    """
    Search YouTube for recent videos that indicate creator and market discourse.

    Args:
        query: Search query for the startup category or user problem
        max_results: Number of videos to return (max 10)

    Returns:
        JSON string with recent YouTube discussion signals
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return missing_config_response(
            tool_name="YouTube Market Signal",
            env_vars=["YOUTUBE_API_KEY"],
            note="Creator and video discourse analysis will be skipped.",
        )

    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return error_response("YouTube Market Signal", "A non-empty query is required")

    published_after = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat().replace("+00:00", "Z")
    try:
        result_count = max(1, min(int(max_results or 5), 10))
    except (TypeError, ValueError):
        result_count = 5
    params = {
        "part": "snippet",
        "q": cleaned_query[:500],
        "type": "video",
        "order": "relevance",
        "maxResults": result_count,
        "publishedAfter": published_after,
        "key": api_key,
    }

    try:
        logger.info("Searching YouTube market signal for: %s", cleaned_query)
        response = httpx.get(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        logger.error("YouTube search failed: %s", exc)
        return error_response("YouTube Market Signal", str(exc), query=cleaned_query)

    videos = []
    sources = []
    for item in payload.get("items", [])[:result_count]:
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {}) or {}
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        title = snippet.get("title") or "Untitled video"
        channel = snippet.get("channelTitle") or "Unknown channel"
        published_at = snippet.get("publishedAt") or ""
        description = clip_text(snippet.get("description") or "", 220)

        videos.append(
            {
                "title": title,
                "channel": channel,
                "published_at": published_at,
                "url": url,
                "description": description,
            }
        )
        sources.append(
            {
                "source_type": "youtube",
                "title": title,
                "url": url,
                "insight": f"{channel} published on {published_at[:10] or 'recent date'}",
            }
        )

    total_results = int(payload.get("pageInfo", {}).get("totalResults") or len(videos))
    return json_response(
        {
            "query": cleaned_query,
            "provider": "youtube",
            "results_found": total_results,
            "creator_discourse_signal": _classify_discourse(total_results),
            "videos": videos,
            "sources": sources,
        }
    )


def _classify_discourse(total_results: int) -> str:
    if total_results >= 1000:
        return "ACTIVE"
    if total_results >= 100:
        return "EMERGING"
    if total_results > 0:
        return "LIMITED"
    return "NONE"
