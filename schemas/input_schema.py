"""MIP-003 compliant input schema for the Idea Validation Agent.

The agent is human-in-the-loop: it only asks for the idea (and an optional
feedback tone) up front, then gathers everything else through dynamic
clarifying questions via /provide_input.
"""
from typing import Any, Dict, List, Tuple

FEEDBACK_TONE_VALUES = [
    "Brutally Honest — no sugarcoating, tell me the hard truth",
    "Constructive — balanced feedback with improvement suggestions",
    "Roast Me — savage, funny, but still insightful",
]

DEFAULT_FEEDBACK_TONE = FEEDBACK_TONE_VALUES[1]

INPUT_SCHEMA = {
    "input_data": [
        {
            "id": "idea",
            "type": "string",
            "name": "Your Idea",
            "data": {
                "description": (
                    "In a few sentences, describe the idea you want validated. "
                    "The agent will research it, then ask you follow-up questions "
                    "before producing the final report."
                )
            },
            "validations": [
                {"validation": "min", "value": "30"}
            ],
        },
        {
            "id": "feedback_tone",
            "type": "option",
            "name": "Feedback Style (optional)",
            "data": {"values": FEEDBACK_TONE_VALUES},
            "validations": [
                {"validation": "optional", "value": "true"},
                {"validation": "max", "value": "1"},
            ],
        },
    ]
}


def parse_input_data(input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Parse MIP-003 list-of-pairs input_data into a flat dict."""
    return {item["key"]: item["value"] for item in input_data}


def validate_required_fields(parsed_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the minimal initial input. Only `idea` is required."""
    errors: List[str] = []

    idea = (parsed_data.get("idea") or "").strip()
    if not idea:
        errors.append("Missing required field: idea")
    elif len(idea) < 30:
        errors.append("idea must be at least 30 characters")

    return (len(errors) == 0, errors)
