#!/usr/bin/env python3
"""
Idea Validation Agent — core job handler.

Human-in-the-loop flow:
  1. Accept a single idea (and optional tone).
  2. Run a lightweight scoping crew.
  3. Ask the user 3-5 dynamic clarifying questions via MIP-003 /provide_input.
  4. Run the full VC/market/technical deep-research crew.
  5. Present the draft report and ask the user to approve or request changes.
  6. If changes are requested, rewrite the report and loop back to step 5.
"""
import logging
import sys
from typing import Any, Dict, List

from masumi.hitl import request_input

logger = logging.getLogger(__name__)

MAX_REFINEMENT_ROUNDS = 5  # safety cap; loop normally ends on user approval


async def process_job(identifier_from_purchaser: str, input_data: Dict[str, Any]) -> str:
    """Top-level job handler wired into Masumi's /start_job route."""
    try:
        logger.info("Starting idea validation job for purchaser: %s", identifier_from_purchaser)
        logger.info("Input data keys: %s", list(input_data.keys()))

        major, minor = sys.version_info[:2]
        if (major, minor) >= (3, 14):
            version = f"{major}.{minor}"
            logger.error("Unsupported Python runtime detected: %s", version)
            return _build_error_report(
                title="Runtime Error",
                summary=f"Unsupported Python runtime `{version}`.",
                details=[
                    "CrewAI requires Python >=3.10 and <3.14.",
                    "Run this agent with Python 3.13.",
                ],
            )

        from schemas.input_schema import validate_required_fields, DEFAULT_FEEDBACK_TONE
        from crew_definition import (
            run_scoping_crew,
            run_deep_crew,
            run_refinement_crew,
        )
        from clarifying import generate_clarifying_questions
        from config import get_settings

        settings = get_settings()

        is_valid, errors = validate_required_fields(input_data)
        if not is_valid:
            logger.error("Input validation failed: %s", errors)
            return _build_error_report(
                title="Validation Failed",
                summary="Input validation failed.",
                details=errors,
            )

        if not settings.anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY not configured")
            return _build_error_report(
                title="Configuration Error",
                summary="ANTHROPIC_API_KEY is required but not set.",
                details=["ANTHROPIC_API_KEY not set in environment"],
            )

        idea = str(input_data.get("idea") or "").strip()
        feedback_tone = str(input_data.get("feedback_tone") or DEFAULT_FEEDBACK_TONE).strip()

        logger.info("Idea (truncated): %s...", idea[:120])
        logger.info("Feedback tone: %s", feedback_tone)

        # ── Phase 1: scoping ────────────────────────────────────────────────
        logger.info("Phase 1: running scoping crew")
        scoping_summary = await run_scoping_crew(
            idea=idea,
            anthropic_api_key=settings.anthropic_api_key,
            anthropic_model=settings.anthropic_model,
        )

        # ── Phase 2: clarifying questions via HITL ─────────────────────────
        logger.info("Phase 2: generating clarifying questions")
        hitl_request = await generate_clarifying_questions(
            idea=idea,
            scoping_summary=scoping_summary,
            anthropic_api_key=settings.anthropic_api_key,
            anthropic_model=settings.anthropic_model,
        )
        intro_message = _compose_clarifying_message(hitl_request["message"], scoping_summary)

        logger.info("Phase 2: pausing for /provide_input (clarifying questions)")
        answers = await request_input(hitl_request["input_schema"], message=intro_message)
        answers = _sanitize_answers(answers)
        logger.info("Phase 2: received answers for keys: %s", list(answers.keys()))

        # ── Phase 3: deep research crew ─────────────────────────────────────
        logger.info("Phase 3: running deep research crew")
        deep_result = await run_deep_crew(
            idea=idea,
            answers=answers,
            feedback_tone=feedback_tone,
            anthropic_api_key=settings.anthropic_api_key,
            anthropic_model=settings.anthropic_model,
        )

        if deep_result.get("status") == "failed":
            logger.error("Deep crew failed: %s", deep_result.get("error"))
            return _build_error_report(
                title="Validation Failed",
                summary=deep_result.get("error", "An error occurred during analysis."),
                details=deep_result.get("details", []),
            )

        report_markdown = deep_result.get("full_report_markdown", "")
        if not report_markdown:
            logger.warning("Deep crew returned empty report")
            return _build_error_report(
                title="Validation Report Error",
                summary="No content was generated.",
            )

        # ── Phase 4: review/refine loop ─────────────────────────────────────
        for round_index in range(1, MAX_REFINEMENT_ROUNDS + 1):
            logger.info("Phase 4: review round %s — pausing for approval", round_index)
            review = await request_input(
                _review_schema(),
                message=_review_message(report_markdown, round_index),
            )
            approved = _interpret_boolean(review.get("approve"), default=False)
            user_feedback = str(review.get("feedback") or "").strip()

            if approved:
                logger.info("Phase 4: report approved by user at round %s", round_index)
                break

            if not user_feedback:
                logger.info("Phase 4: user did not approve and provided no feedback — stopping loop")
                break

            logger.info("Phase 4: refining report based on feedback (round %s)", round_index)
            report_markdown = await run_refinement_crew(
                previous_report=report_markdown,
                user_feedback=user_feedback,
                feedback_tone=feedback_tone,
                anthropic_api_key=settings.anthropic_api_key,
                anthropic_model=settings.anthropic_model,
            ) or report_markdown
        else:
            logger.info("Phase 4: hit MAX_REFINEMENT_ROUNDS, returning latest draft")

        return _build_completed_report(
            identifier_from_purchaser=identifier_from_purchaser,
            report_markdown=report_markdown,
            verdict=_extract_verdict(report_markdown),
            execution_metadata=deep_result.get("execution_metadata", {}),
            research_methodology=deep_result.get("research_methodology", {}),
            source_register=deep_result.get("source_register", []),
            analysis_summary=deep_result.get("analysis_summary", {}),
        )

    except Exception as e:
        logger.error("Error processing idea validation job: %s", e, exc_info=True)
        return _build_error_report(
            title="Validation Error",
            summary="An unexpected error occurred during analysis.",
            details=[str(e)],
        )


# ─────────────────────────────────────────────────────────────────────────────
# HITL helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compose_clarifying_message(llm_message: str, scoping_summary: Dict[str, Any]) -> str:
    parts: List[str] = [llm_message.strip()]
    industry = scoping_summary.get("industry_hypothesis")
    audience = scoping_summary.get("likely_audience")
    if industry or audience:
        parts.append("")
        parts.append("My quick read so far:")
        if industry:
            parts.append(f"- Industry hypothesis: {industry}")
        if audience:
            parts.append(f"- Likely audience: {audience}")
    return "\n".join(parts).strip()


def _review_schema() -> Dict[str, Any]:
    return {
        "input_data": [
            {
                "id": "approve",
                "type": "boolean",
                "name": "Approve this report?",
                "data": {
                    "description": (
                        "Yes finalizes the report and ends the session. "
                        "No lets you ask for specific changes below."
                    )
                },
            },
            {
                "id": "feedback",
                "type": "string",
                "name": "What should change? (optional — leave blank to accept as-is)",
                "data": {
                    "description": (
                        "If you said No above, describe what to rewrite, "
                        "expand, or challenge. Leave blank to stop iterating."
                    )
                },
                "validations": [{"validation": "optional", "value": "true"}],
            },
        ]
    }


def _review_message(report_markdown: str, round_index: int) -> str:
    header = "Draft validation report" if round_index == 1 else f"Revised draft (round {round_index})"
    return (
        f"{header}. Review it, then either approve to finalize or describe "
        "what you want changed.\n\n" + report_markdown.strip()
    )


def _sanitize_answers(answers: Any) -> Dict[str, Any]:
    if not isinstance(answers, dict):
        return {}
    cleaned: Dict[str, Any] = {}
    for key, value in answers.items():
        if value in (None, "", [], {}):
            continue
        cleaned[str(key)] = value
    return cleaned


def _interpret_boolean(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "y", "1", "approve", "approved"):
            return True
        if normalized in ("false", "no", "n", "0", "reject", "rejected"):
            return False
    return default


# ─────────────────────────────────────────────────────────────────────────────
# Report assembly (unchanged from previous VC agent)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_verdict(markdown_report: str) -> str:
    verdict_keywords = [
        "STRONG OPPORTUNITY",
        "PROMISING",
        "NEEDS WORK",
        "HIGH RISK",
        "DO NOT PURSUE",
        "STRONG GO",
        "CONDITIONAL GO",
        "WEAK NO",
        "STRONG NO",
    ]
    for keyword in verdict_keywords:
        if keyword in markdown_report:
            return keyword
    return "See full report for verdict"


def _build_completed_report(
    identifier_from_purchaser: str,
    report_markdown: str,
    verdict: str,
    execution_metadata: Dict[str, Any],
    research_methodology: Dict[str, Any],
    source_register: List[Dict[str, str]],
    analysis_summary: Dict[str, Any],
) -> str:
    lines = [
        "# Idea Validation Report",
        "",
        "## Engagement Snapshot",
        "",
        "| Item | Assessment |",
        "| --- | --- |",
        f"| Verdict | {verdict} |",
        f"| Viability Score | {analysis_summary.get('viability_score', 'See scorecard below')} |",
        f"| Confidence | {analysis_summary.get('confidence', 'See scorecard below')} |",
        f"| Recommendation | {analysis_summary.get('go_no_go', 'See full report')} |",
        f"| Analysis Model | {execution_metadata.get('anthropic_model', 'n/a')} |",
        f"| Reference ID | `{identifier_from_purchaser}` |",
        "",
        "---",
        "",
        report_markdown.strip(),
    ]

    methodology_lines = _format_methodology_section(research_methodology, execution_metadata)
    if methodology_lines:
        lines.extend(["", "---", "", "## Methodology & Coverage", "", *methodology_lines])

    lines.extend(["", "---", "", "## Sources & References", ""])
    lines.extend(_format_sources(source_register))

    return "\n".join(lines).strip() + "\n"


def _format_methodology_section(
    research_methodology: Dict[str, Any],
    execution_metadata: Dict[str, Any],
) -> List[str]:
    tools_used = research_methodology.get("tools_used") or []
    limitations = research_methodology.get("limitations") or []
    coverage_notes = research_methodology.get("coverage_notes") or []
    data_quality = research_methodology.get("data_quality")

    lines: List[str] = []
    if tools_used:
        lines.append(f"- Tools used: {', '.join(str(tool) for tool in tools_used)}")
    else:
        lines.append("- Tools used: Google Trends, web search, and optional website/deck analysis where available.")

    if data_quality:
        lines.append(f"- Evidence quality: {data_quality}")
    if execution_metadata.get("source_count") is not None:
        lines.append(f"- Sources captured: {execution_metadata.get('source_count', 0)}")
    if coverage_notes:
        lines.append(f"- Coverage notes: {'; '.join(str(note) for note in coverage_notes if note)}")
    if limitations:
        joined = "; ".join(str(limitation) for limitation in limitations if limitation)
        lines.append(f"- Research limitations: {joined}")
    else:
        lines.append("- Research limitations: Some inputs may rely on public web data and model interpretation where direct market data is sparse.")

    return lines


def _format_sources(source_register: List[Dict[str, str]]) -> List[str]:
    if not source_register:
        return [
            "1. No machine-readable source list was captured in this run.",
            "2. The analysis still used the configured research tools, but explicit URL-level references were not preserved by the model output.",
        ]

    lines: List[str] = []
    for index, source in enumerate(source_register, start=1):
        title = source.get("title", "Untitled source")
        url = source.get("url", "")
        source_type = source.get("source_type", "research")
        insight = source.get("insight", "")

        line = f"{index}. **{title}**"
        if url:
            line += f" ({url})"
        line += f" [{source_type}]"
        if insight:
            line += f" - {insight}"
        lines.append(line)

    return lines


def _build_error_report(title: str, summary: str, details: List[str] | str | None = None) -> str:
    lines = [f"# {title}", "", summary]
    if details:
        detail_items = [details] if isinstance(details, str) else details
        lines.extend(["", "## Details", ""])
        lines.extend(f"- {detail}" for detail in detail_items if detail)
    return "\n".join(lines).strip() + "\n"
