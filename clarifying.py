"""Generate clarifying questions for the Idea Validation Agent.

Given an idea + the scoping-research summary, ask Claude to draft 3-5
follow-up questions in MIP-003 input_data schema format so the Masumi
`/provide_input` endpoint can collect answers from the user.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List

from anthropic import Anthropic

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a VC analyst preparing clarifying questions for a founder.

You will receive:
- The founder's idea (short text).
- A JSON summary of initial scoping research (industry hypothesis, likely audience, possible competitors, business-model guesses).

Your task: produce 3 to 5 follow-up questions that fill the biggest gaps before a full VC/market/technical deep-dive. Good questions:
- Confirm or correct your scoping hypotheses (industry, audience, model).
- Ask about founder stage, traction, unique advantage, and primary goal of this validation.
- Skip anything already obvious from the idea text.

Return STRICT JSON matching this shape — no markdown, no prose:
{
  "message": "<one-sentence intro shown to the user>",
  "questions": [
    {
      "id": "<snake_case_field_id>",
      "type": "string" | "option",
      "name": "<the question as a short label>",
      "description": "<one-line helper text>",
      "required": true | false,
      "values": ["opt1", "opt2", ...]   // only for type=option
    }
  ]
}

Rules:
- Use type=option when there is a short, well-defined list of choices (e.g. stage, business model).
- Use type=string for open-ended answers (e.g. unique advantage, traction details).
- Keep ids in snake_case. Do not reuse id "idea" or "feedback_tone".
- Maximum 5 questions. No nested objects.
"""


async def generate_clarifying_questions(
    idea: str,
    scoping_summary: Dict[str, Any],
    anthropic_api_key: str,
    anthropic_model: str,
) -> Dict[str, Any]:
    """Return a MIP-003 request_input payload: {"message", "input_schema"}.

    The input_schema is a dict with an "input_data" list, ready to pass
    straight to masumi.hitl.request_input.
    """
    client = Anthropic(api_key=anthropic_api_key)

    user_payload = json.dumps(
        {"idea": idea, "scoping_summary": scoping_summary},
        ensure_ascii=False,
        default=str,
    )

    def _call_model() -> str:
        response = client.messages.create(
            model=_strip_provider_prefix(anthropic_model),
            max_tokens=1200,
            temperature=0.3,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_payload}],
        )
        parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
        return "\n".join(parts).strip()

    raw_text = await asyncio.to_thread(_call_model)
    parsed = _parse_json_object(raw_text)

    message = str(parsed.get("message") or "").strip() or (
        "I've done a quick scan of your idea. Answer a few follow-ups so I can "
        "run the full validation report."
    )
    questions = parsed.get("questions") or []
    if not isinstance(questions, list) or not questions:
        questions = _fallback_questions()

    input_data = [_question_to_mip003(q) for q in questions if isinstance(q, dict)]
    input_data = [item for item in input_data if item is not None][:5]
    if not input_data:
        input_data = [_question_to_mip003(q) for q in _fallback_questions()]

    return {
        "message": message,
        "input_schema": {"input_data": input_data},
    }


def _question_to_mip003(question: Dict[str, Any]) -> Dict[str, Any] | None:
    raw_id = str(question.get("id") or "").strip()
    field_id = re.sub(r"[^a-z0-9_]", "_", raw_id.lower()).strip("_")
    if not field_id or field_id in ("idea", "feedback_tone"):
        return None

    name = str(question.get("name") or field_id.replace("_", " ").title()).strip()
    description = str(question.get("description") or "").strip()
    qtype = (question.get("type") or "string").strip().lower()
    required = bool(question.get("required", False))

    if qtype == "option":
        values = question.get("values") or []
        values = [str(v).strip() for v in values if str(v).strip()]
        if not values:
            qtype = "string"

    item: Dict[str, Any] = {
        "id": field_id,
        "type": qtype if qtype in ("string", "option", "boolean") else "string",
        "name": name,
        "data": {},
    }
    validations: List[Dict[str, str]] = []

    if item["type"] == "option":
        item["data"]["values"] = values  # type: ignore[possibly-unbound]
        validations.append({"validation": "max", "value": "1"})
        if required:
            validations.append({"validation": "min", "value": "1"})
        else:
            validations.append({"validation": "optional", "value": "true"})
    else:
        if description:
            item["data"]["description"] = description
        if not required:
            validations.append({"validation": "optional", "value": "true"})

    if validations:
        item["validations"] = validations
    return item


def _fallback_questions() -> List[Dict[str, Any]]:
    """Used when the LLM fails to produce a usable schema."""
    return [
        {
            "id": "founder_stage",
            "type": "option",
            "name": "What stage are you at?",
            "required": True,
            "values": [
                "Just an idea — haven't started building",
                "Early stage — MVP or prototype",
                "Growth stage — users or revenue",
                "Scaling — raising investment",
            ],
        },
        {
            "id": "target_audience",
            "type": "string",
            "name": "Who exactly is this for?",
            "description": "The specific customer or user you're building for.",
            "required": False,
        },
        {
            "id": "known_competitors",
            "type": "string",
            "name": "Any competitors you already know about?",
            "description": "List names or URLs, or say 'none that I know of'.",
            "required": False,
        },
        {
            "id": "unique_advantage",
            "type": "string",
            "name": "What's your unfair advantage?",
            "description": "Why can you win — tech, data, network, distribution, expertise?",
            "required": False,
        },
        {
            "id": "primary_goal",
            "type": "option",
            "name": "What do you want out of this validation?",
            "required": False,
            "values": [
                "Decide whether to build it at all",
                "Sharpen the idea before building",
                "Prepare for fundraising",
                "Decide whether to pivot",
                "Honest outside opinion",
            ],
        },
    ]


def _strip_provider_prefix(model_name: str) -> str:
    name = (model_name or "").strip()
    if name.startswith("anthropic/"):
        return name.split("/", 1)[1]
    return name or "claude-3-5-sonnet-latest"


def _parse_json_object(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if not cleaned:
        return {}
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    for candidate in (cleaned, _largest_braced(cleaned)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    logger.warning("Clarifying-questions LLM response was not valid JSON; using fallback")
    return {}


def _largest_braced(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return ""
    return text[start : end + 1]
