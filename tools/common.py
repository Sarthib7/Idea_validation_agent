"""Shared helpers for external research tools."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable
from urllib.parse import urlparse


def json_response(payload: Dict[str, Any]) -> str:
    """Serialize tool payloads consistently."""
    return json.dumps(payload, indent=2, ensure_ascii=True)


def error_response(tool_name: str, message: str, **extra: Any) -> str:
    """Return a structured error payload."""
    payload: Dict[str, Any] = {
        "tool": tool_name,
        "error": message,
    }
    for key, value in extra.items():
        if value not in (None, "", [], {}):
            payload[key] = value
    return json_response(payload)


def missing_config_response(tool_name: str, env_vars: Iterable[str], note: str = "") -> str:
    """Return a standard missing-config response."""
    return error_response(
        tool_name=tool_name,
        message="Required API credentials are not configured",
        missing_env_vars=list(env_vars),
        note=note,
    )


def normalize_domain(value: str) -> str:
    """Extract a clean domain from a URL or domain string."""
    raw = (value or "").strip()
    if not raw:
        return ""

    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)
    domain = (parsed.netloc or parsed.path or "").strip().lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.split("/")[0]


def clip_text(value: str, limit: int = 220) -> str:
    """Trim long strings to keep tool payloads compact."""
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def dig_first(value: Any, *paths: tuple[str, ...]) -> Any:
    """Return the first non-empty value found along nested dict paths."""
    for path in paths:
        current = value
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current not in (None, "", [], {}):
            return current
    return None
