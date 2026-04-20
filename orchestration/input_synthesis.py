"""LLM-driven mapping of VC validation inputs onto a hired agent's schema.

A Sokosumi agent's input schema is the same MIP-003 ``input_data`` block we
expose ourselves: a list of fields with ``id``, ``type``, ``name``, optional
``data.values`` (for option/select fields), and ``data.description``. To hire
the agent we need to feed it a value for every required field that makes
sense given the founder's idea.

Rather than hard-code field-by-field heuristics for every external agent,
we ask Anthropic's Claude to do the mapping for us. Claude is a perfect fit
because:

* the VC inputs are unstructured prose,
* the target schema is fully self-describing, and
* we already have an Anthropic key wired in for the rest of the crew.

The synthesizer is intentionally defensive: it always returns *some* mapping,
falls back to a deterministic best-effort map if Claude is unreachable, and
respects ``option`` field allowed values exactly so the Sokosumi job creation
endpoint will accept the payload.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are an integration assistant. You will be given:

1. A description of a startup idea collected by a VC validation agent.
2. The MIP-003 input schema of an external research agent we want to hire.

Your job is to produce a JSON object that maps each schema field id to a
realistic, useful value derived strictly from the startup context. Follow
these rules:

- Output ONLY a single JSON object — no prose, no Markdown fences.
- The keys must be the exact field ids from the schema.
- For type "string": return a concise but information-rich string. Prefer
  text that the external research agent can act on (e.g. specific keywords,
  company names, geographies). Never invent facts the founder did not say.
- For type "option": pick exactly one value from the supplied "values"
  array, copying it verbatim.
- If the schema lists an option as a multi-select (validations: max > 1),
  return an array of values, all from the supplied list.
- For type "number": return a number (not a string).
- For type "boolean": return true or false.
- If a field is genuinely optional and you have no relevant information,
  use an empty string for strings or omit the field entirely for options.
- Never echo placeholder text. Never include keys that are not in the
  schema.
"""


def _get_field_validations(field: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for v in field.get("validations") or []:
        if isinstance(v, dict):
            key = str(v.get("validation") or "").strip()
            val = str(v.get("value") or "").strip()
            if key:
                out[key] = val
    return out


def _is_optional_field(field: Dict[str, Any]) -> bool:
    validations = _get_field_validations(field)
    if validations.get("optional", "").lower() == "true":
        return True
    if "min" not in validations:
        return True
    return False


def _build_user_prompt(idea_payload: Dict[str, Any], input_schema: Dict[str, Any]) -> str:
    fields_block = json.dumps(input_schema.get("input_data", []), indent=2, ensure_ascii=False)
    idea_block = json.dumps(idea_payload, indent=2, ensure_ascii=False)
    return (
        "Startup context (from the VC validation agent's user form):\n"
        f"{idea_block}\n\n"
        "External agent input schema (MIP-003 input_data array):\n"
        f"{fields_block}\n\n"
        "Return the JSON mapping now."
    )


def _strip_json_block(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _coerce_to_object(text: str) -> Dict[str, Any]:
    cleaned = _strip_json_block(text)
    if not cleaned:
        return {}
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _enforce_option_fields(
    mapping: Dict[str, Any], input_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Constrain option fields to the allowed values.

    Sokosumi rejects option payloads whose value isn't in the schema's
    ``data.values`` list. The model is usually obedient but we double-check.
    """
    sanitized: Dict[str, Any] = {}
    for field in input_schema.get("input_data", []):
        if not isinstance(field, dict):
            continue
        field_id = field.get("id")
        if not field_id:
            continue
        if field_id not in mapping:
            continue

        value = mapping[field_id]
        if field.get("type") == "option":
            allowed = list((field.get("data") or {}).get("values") or [])
            if not allowed:
                sanitized[field_id] = value
                continue

            if isinstance(value, list):
                kept = [v for v in value if v in allowed]
                if not kept:
                    kept = [allowed[0]]
                validations = _get_field_validations(field)
                max_count = int(validations.get("max", "1") or "1")
                sanitized[field_id] = kept[:max_count] if max_count > 1 else kept[0]
            elif isinstance(value, str):
                sanitized[field_id] = value if value in allowed else allowed[0]
            else:
                sanitized[field_id] = allowed[0]
        else:
            sanitized[field_id] = value

    return sanitized


def _fallback_synthesis(
    idea_payload: Dict[str, Any], input_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Deterministic best-effort mapping used when the LLM call fails."""
    idea = (idea_payload.get("idea_description") or "").strip()
    industry = (idea_payload.get("industry") or "").strip()
    audience = (idea_payload.get("target_audience") or "").strip()
    competitors = (idea_payload.get("competitors") or "").strip()

    base_text_pool = [
        f"Startup idea: {idea}" if idea else "",
        f"Industry: {industry}" if industry else "",
        f"Target audience: {audience}" if audience else "",
        f"Known competitors: {competitors}" if competitors else "",
    ]
    base_text = "\n".join(part for part in base_text_pool if part).strip() or idea

    out: Dict[str, Any] = {}
    for field in input_schema.get("input_data", []):
        if not isinstance(field, dict):
            continue
        field_id = field.get("id")
        field_type = field.get("type")
        if not field_id:
            continue

        if field_type == "option":
            allowed = list((field.get("data") or {}).get("values") or [])
            if allowed:
                validations = _get_field_validations(field)
                max_count = int(validations.get("max", "1") or "1")
                out[field_id] = [allowed[0]] if max_count > 1 else allowed[0]
            elif not _is_optional_field(field):
                out[field_id] = ""
        elif field_type == "number":
            if not _is_optional_field(field):
                out[field_id] = 0
        elif field_type == "boolean":
            if not _is_optional_field(field):
                out[field_id] = False
        else:
            if not _is_optional_field(field):
                out[field_id] = base_text or "Validate this startup idea."
            else:
                truncated = base_text[:600]
                if truncated:
                    out[field_id] = truncated
    return out


async def synthesize_input(
    *,
    idea_payload: Dict[str, Any],
    input_schema: Dict[str, Any],
    anthropic_api_key: str,
    anthropic_model: str = "claude-3-5-sonnet-latest",
) -> Dict[str, Any]:
    """Build an input_data dict that satisfies a hired agent's schema.

    Args:
        idea_payload: The validation agent's parsed user input (key/value).
        input_schema: ``GET /agents/{id}/input-schema`` ``data`` payload.
        anthropic_api_key: API key for the Anthropic Messages API.
        anthropic_model: Model alias used for the synthesis call.

    Returns:
        A dict ``{field_id: value}`` ready to send as ``inputData`` on the
        Sokosumi job creation endpoint.
    """
    if not isinstance(input_schema, dict) or "input_data" not in input_schema:
        logger.warning("Input schema is missing 'input_data'; using fallback")
        return _fallback_synthesis(idea_payload, input_schema or {})

    if not anthropic_api_key:
        logger.warning("No Anthropic key for input synthesis; using fallback")
        return _enforce_option_fields(
            _fallback_synthesis(idea_payload, input_schema), input_schema
        )

    try:
        from anthropic import AsyncAnthropic
    except ImportError:
        logger.warning("anthropic package missing; using fallback synthesis")
        return _enforce_option_fields(
            _fallback_synthesis(idea_payload, input_schema), input_schema
        )

    client = AsyncAnthropic(api_key=anthropic_api_key)
    user_prompt = _build_user_prompt(idea_payload, input_schema)

    try:
        response = await client.messages.create(
            model=anthropic_model,
            max_tokens=1500,
            temperature=0.2,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # pragma: no cover - network/auth failures
        logger.warning("Anthropic synthesis call failed (%s); using fallback", exc)
        return _enforce_option_fields(
            _fallback_synthesis(idea_payload, input_schema), input_schema
        )

    raw_text = ""
    try:
        for block in getattr(response, "content", []) or []:
            if getattr(block, "type", None) == "text":
                raw_text += block.text or ""
    except Exception:  # pragma: no cover - defensive
        raw_text = ""

    mapping = _coerce_to_object(raw_text)
    if not mapping:
        logger.warning("LLM returned empty/non-JSON synthesis; using fallback")
        return _enforce_option_fields(
            _fallback_synthesis(idea_payload, input_schema), input_schema
        )

    sanitized = _enforce_option_fields(mapping, input_schema)

    # Backfill any required fields the model omitted using the deterministic
    # fallback so the Sokosumi POST doesn't 400 us.
    fallback = _fallback_synthesis(idea_payload, input_schema)
    for required_field_id, required_value in fallback.items():
        if required_field_id not in sanitized:
            sanitized[required_field_id] = required_value

    return sanitized


def field_summary(input_schema: Dict[str, Any]) -> List[str]:
    """Compact, human-readable summary of the schema for log lines."""
    out: List[str] = []
    for field in input_schema.get("input_data", []) or []:
        if not isinstance(field, dict):
            continue
        field_id = field.get("id") or "?"
        field_type = field.get("type") or "?"
        optional = _is_optional_field(field)
        out.append(f"{field_id}:{field_type}{'?' if optional else ''}")
    return out


__all__ = ["synthesize_input", "field_summary"]
