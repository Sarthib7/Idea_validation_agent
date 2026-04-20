"""Web search tool using SerpApi or SerperDev"""
import logging
import os
from typing import Dict, Any
from crewai.tools import tool
import json

logger = logging.getLogger(__name__)


@tool("Web Search")
def web_search_tool(query: str, search_type: str = "competitors") -> str:
    """
    Search the web for market intelligence, competitors, and industry news.

    Args:
        query: Search query
        search_type: Type of search - "competitors", "market_size", "funding", or "news"

    Returns:
        JSON string with search results
    """
    try:
        # Check which API is configured
        serpapi_key = os.getenv("SERPAPI_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")

        if not serpapi_key and not serper_key:
            return json.dumps({
                "error": "No search API key configured",
                "message": "Set SERPAPI_API_KEY or SERPER_API_KEY environment variable"
            })

        logger.info(f"Searching web for: {query} (type: {search_type})")

        # Use SerperDev if available (preferred - simpler API)
        if serper_key:
            return _search_with_serper(query, serper_key)
        else:
            return _search_with_serpapi(query, serpapi_key)

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return json.dumps({"error": str(e)})


def _search_with_serper(query: str, api_key: str) -> str:
    """Search using SerperDev API"""
    import httpx

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": 10
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        # Extract organic results
        results = []
        for item in data.get("organic", [])[:10]:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            })

        return json.dumps({
            "query": query,
            "results_count": len(results),
            "results": results
        }, indent=2)

    except Exception as e:
        logger.error(f"SerperDev search failed: {e}")
        return json.dumps({"error": str(e)})


def _search_with_serpapi(query: str, api_key: str) -> str:
    """Search using SerpApi"""
    from serpapi import GoogleSearch

    try:
        params = {
            "q": query,
            "api_key": api_key,
            "num": 10,
            "engine": "google"
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        # Extract organic results
        results = []
        for item in data.get("organic_results", [])[:10]:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0)
            })

        return json.dumps({
            "query": query,
            "results_count": len(results),
            "results": results
        }, indent=2)

    except Exception as e:
        logger.error(f"SerpApi search failed: {e}")
        return json.dumps({"error": str(e)})
