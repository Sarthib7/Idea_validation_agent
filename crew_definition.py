"""CrewAI crew definitions for the Idea Validation Agent.

The agent runs in phases:
  1. Scoping crew — lightweight pass on the raw idea. Output is consumed by
     the clarifying-question generator and later by the deep crew.
  2. Deep crew — full market / VC / report pipeline, parameterised by the
     user's answers to clarifying questions.
  3. Refinement task — single-agent task that rewrites the report based on
     user feedback collected via HITL.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List

from crewai import Agent, Crew, Task, Process, LLM

from tools import (
    google_trends_tool,
    web_search_tool,
    website_scraper_tool,
    file_analyzer_tool,
    news_intelligence_tool,
    github_ecosystem_tool,
    similarweb_competitor_tool,
    youtube_market_signal_tool,
)

logger = logging.getLogger(__name__)

# Dated Anthropic model IDs (Messages API). Avoid ``*-latest`` aliases — they can 404
# depending on SDK/API routing. See Anthropic docs for current snapshots.
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_MODEL_FALLBACKS = (
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
)


def _patch_crewai_disable_strict_tool_schemas() -> None:
    """CrewAI marks every tool with OpenAI-style ``strict: true`` (agent_utils).

    Anthropic returns 400 for some Claude models: model does not support strict tools.
    We keep tool schemas but turn off strict mode so native tool use works.
    """
    try:
        from crewai.utilities import agent_utils as _au
    except ImportError:
        return
    if getattr(_au.convert_tools_to_openai_schema, "_idea_validation_patched", False):
        return

    _original = _au.convert_tools_to_openai_schema

    def _convert_without_strict(tools):
        openai_tools, available_functions, tool_name_mapping = _original(tools)
        for spec in openai_tools:
            fn = spec.get("function")
            if isinstance(fn, dict):
                fn["strict"] = False
        return openai_tools, available_functions, tool_name_mapping

    setattr(_convert_without_strict, "_idea_validation_patched", True)
    _au.convert_tools_to_openai_schema = _convert_without_strict


_patch_crewai_disable_strict_tool_schemas()


def load_prompt(filename: str) -> str:
    """Load a prompt file from the prompts directory."""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", filename)
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("Prompt file not found: %s", prompt_path)
        return f"You are a {filename.replace('.md', '').replace('_', ' ')} agent."


def _make_llm(anthropic_api_key: str, anthropic_model: str, *, max_tokens: int = 4096) -> LLM:
    return LLM(
        model=_normalize_anthropic_model_name(anthropic_model),
        api_key=anthropic_api_key,
        temperature=0.7,
        max_tokens=max_tokens,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Scoping crew
# ─────────────────────────────────────────────────────────────────────────────

def create_scoping_crew(idea: str, anthropic_api_key: str, anthropic_model: str) -> Crew:
    """A quick, single-agent pass that reads the idea and infers context."""
    llm = _make_llm(anthropic_api_key, anthropic_model, max_tokens=2048)

    scout = Agent(
        role="Startup Scoping Analyst",
        goal="Form an initial read on the founder's idea using lightweight research.",
        backstory=(
            "You are a fast-moving VC associate. Given only a short idea "
            "description, you do quick research to infer the industry, likely "
            "audience, obvious competitors, and plausible business models — "
            "enough to draft sharp follow-up questions for the founder."
        ),
        llm=llm,
        tools=[google_trends_tool, web_search_tool],
        verbose=True,
        allow_delegation=False,
    )

    scoping_task = Task(
        description=f"""
        Read this startup idea and do a short scoping pass.

        **Idea**: {idea}

        Use Google Trends + one web search to spot obvious signals. Keep it
        fast — the goal is to understand enough to ask good follow-up questions,
        not to produce a full report.

        Return STRICT JSON with this shape:
        {{
          "industry_hypothesis": "<best guess at the industry/vertical>",
          "likely_audience": "<who the idea seems to target, 1-2 sentences>",
          "possible_business_models": ["<model>", ...],
          "possible_competitors": ["<name or url>", ...],
          "open_questions": ["<the key things you still don't know>", ...],
          "quick_trend_signal": "<growing | declining | stable | unclear>"
        }}
        """,
        agent=scout,
        expected_output="Strict JSON object with scoping fields.",
    )

    return Crew(
        agents=[scout],
        tasks=[scoping_task],
        process=Process.sequential,
        verbose=True,
        full_output=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Deep crew (research + VC analysis + report writing)
# ─────────────────────────────────────────────────────────────────────────────

def create_deep_crew(
    idea: str,
    answers: Dict[str, Any],
    feedback_tone: str,
    anthropic_api_key: str,
    anthropic_model: str,
) -> Crew:
    """Full three-agent deep-dive crew. `answers` is the dict collected from HITL."""
    llm = _make_llm(anthropic_api_key, anthropic_model)

    if "Brutally Honest" in feedback_tone:
        report_prompt = load_prompt("report_writer_brutal.md")
    elif "Roast Me" in feedback_tone:
        report_prompt = load_prompt("report_writer_roast.md")
    else:
        report_prompt = load_prompt("report_writer_constructive.md")

    market_researcher = Agent(
        role="Senior Market Research Analyst",
        goal="Gather comprehensive real-time market intelligence on the startup idea",
        backstory=load_prompt("market_researcher.md"),
        llm=llm,
        tools=[
            google_trends_tool,
            web_search_tool,
            news_intelligence_tool,
            github_ecosystem_tool,
            similarweb_competitor_tool,
            youtube_market_signal_tool,
            website_scraper_tool,
            file_analyzer_tool,
        ],
        verbose=True,
        allow_delegation=False,
    )

    vc_analyst = Agent(
        role="Principal at a Top-Tier VC Fund",
        goal="Apply rigorous VC frameworks to evaluate the startup idea",
        backstory=load_prompt("vc_analyst.md"),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    report_writer = Agent(
        role="Investment Memo Writer",
        goal="Synthesize all analysis into a professional, tone-adjusted validation report",
        backstory=report_prompt,
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    answers_block = _format_answers_block(answers)

    research_task = Task(
        description=f"""
        Conduct comprehensive market research for this startup idea.

        **Idea**: {idea}

        **Founder's answers to follow-up questions**:
        {answers_block}

        Use ALL available tools to:
        1. Analyze market trends (Google Trends)
        2. Research competitors and market size (Web Search)
        3. Pull recent media coverage and narrative momentum (News Intelligence)
        4. Measure developer ecosystem activity for technical markets (GitHub Ecosystem)
        5. Benchmark website/competitor traffic signals when a domain is available (Similarweb)
        6. Capture creator and market discourse (YouTube Market Signal)
        7. Analyze website if the founder provided one
        8. Analyze pitch deck if the founder provided one

        Minimum research standard:
        - Use at least 4 distinct evidence sources when credentials or public access allow it.
        - Include at least 1 source beyond Google Trends + generic web search.
        - If an API is unavailable because credentials are missing, record that explicitly.
        - Prefer structured evidence over generic opinion.

        Return structured research findings with:
        - Trend analysis (growing/declining/stable)
        - Competitor intelligence
        - Market size indicators
        - Media coverage / narrative signal
        - Developer ecosystem signal (for technical products)
        - Traffic benchmark signal (when domains are available)
        - Creator discourse signal
        - Website/deck analysis (if applicable)
        - Methodology notes (tools used, data quality, limitations)
        - Source register with title, URL/domain, source type, and why it matters
        - Data quality assessment
        """,
        agent=market_researcher,
        expected_output="Comprehensive market research report in structured JSON format with all findings",
    )

    analysis_task = Task(
        description=f"""
        Apply VC evaluation frameworks to the market research findings.

        **Idea**: {idea}

        **Founder's answers**:
        {answers_block}

        Apply these frameworks:
        1. Sequoia 10-Point Evaluation
        2. TAM/SAM/SOM Market Sizing
        3. YC 5-Question Filter
        4. Moat Analysis
        5. Unit Economics Assessment

        Generate:
        - 10-dimension scoring matrix (each scored 1-10 with detailed reasoning)
        - Overall viability score (0-100)
        - Verdict (STRONG OPPORTUNITY / PROMISING / NEEDS WORK / HIGH RISK / DO NOT PURSUE)
        - Confidence level (HIGH / MEDIUM / LOW)
        - SWOT analysis
        - Critical risks with severity and mitigation
        - Actionable next steps

        Use the market research data from the previous task as your primary source.
        """,
        agent=vc_analyst,
        expected_output="Complete VC analysis in structured JSON format with all framework evaluations",
        context=[research_task],
    )

    report_task = Task(
        description=f"""
        Write the final validation report using the selected feedback tone.

        **Selected Tone**: {feedback_tone or 'Constructive'}

        Synthesize the market research and VC analysis into a complete validation report.

        The report must include:
        1. Engagement Snapshot (table with Verdict, Score, Confidence, Recommendation)
        2. Executive Summary
        3. Verdict & Scoring Matrix
        4. Investment View (go / conditional go / no-go)
        5. Market Analysis (TAM/SAM/SOM, trends, competitors)
        6. Strengths
        7. Weaknesses
        8. Opportunities
        9. Threats
        10. Critical Risks (severity + mitigation)
        11. Actionable Next Steps (prioritized, with timelines)
        12. Website Feedback (if URL was provided by the founder)
        13. Pitch Deck Feedback (if file was provided by the founder)
        14. Research Methodology
        15. Sources & References (numbered, with URLs/domains when known)
        16. Bottom Line

        Hard constraints:
        - Output pure Markdown only. Do not output JSON.
        - Use tables for the engagement snapshot and scoring matrix.
        - Translate tool output into polished prose, tables, and bullet points.
        - Include actual URLs/domains in Sources & References whenever the research data provides them.
        - If a data source was unavailable, say so explicitly in Research Methodology.
        """,
        agent=report_writer,
        expected_output="Complete validation report in Markdown format with the specified tone applied",
        context=[research_task, analysis_task],
    )

    return Crew(
        agents=[market_researcher, vc_analyst, report_writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True,
        full_output=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Refinement
# ─────────────────────────────────────────────────────────────────────────────

def create_refinement_crew(
    previous_report: str,
    user_feedback: str,
    feedback_tone: str,
    anthropic_api_key: str,
    anthropic_model: str,
) -> Crew:
    """Single-agent crew that rewrites the report to address user feedback."""
    llm = _make_llm(anthropic_api_key, anthropic_model)

    if "Brutally Honest" in feedback_tone:
        report_prompt = load_prompt("report_writer_brutal.md")
    elif "Roast Me" in feedback_tone:
        report_prompt = load_prompt("report_writer_roast.md")
    else:
        report_prompt = load_prompt("report_writer_constructive.md")

    editor = Agent(
        role="Investment Memo Editor",
        goal="Revise the validation report based on the founder's feedback.",
        backstory=report_prompt,
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
        Revise the validation report below to address the founder's feedback.
        Keep the tone ({feedback_tone or 'Constructive'}) and the overall
        structure (Engagement Snapshot, Executive Summary, Scoring Matrix,
        Investment View, SWOT, Risks, Next Steps, Methodology, Sources,
        Bottom Line). Rewrite only what needs to change.

        **Founder's feedback on the previous draft**:
        {user_feedback or '(no feedback provided — polish and tighten the report)'}

        **Previous report**:
        {previous_report}

        Output pure Markdown only. Do not output JSON or prefatory text.
        """,
        agent=editor,
        expected_output="Revised validation report in Markdown.",
    )

    return Crew(
        agents=[editor],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        full_output=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Runner helpers
# ─────────────────────────────────────────────────────────────────────────────

async def run_scoping_crew(
    idea: str,
    anthropic_api_key: str,
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL,
) -> Dict[str, Any]:
    """Run the scoping crew and return the structured scoping summary."""
    async def _build(model_name: str) -> Crew:
        return create_scoping_crew(idea, anthropic_api_key, model_name)

    crew = await _kickoff_with_fallbacks(_build, anthropic_model)
    payload = _extract_task_payload(crew.tasks[0]) if crew.tasks else {}
    return payload or {"open_questions": [], "possible_competitors": []}


async def run_deep_crew(
    idea: str,
    answers: Dict[str, Any],
    feedback_tone: str,
    anthropic_api_key: str,
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL,
) -> Dict[str, Any]:
    """Run the full deep crew. Returns markdown + extracted metadata."""
    async def _build(model_name: str) -> Crew:
        return create_deep_crew(
            idea=idea,
            answers=answers,
            feedback_tone=feedback_tone,
            anthropic_api_key=anthropic_api_key,
            anthropic_model=model_name,
        )

    try:
        crew, model_used = await _kickoff_with_fallbacks(_build, anthropic_model, return_model=True)
    except Exception as e:
        logger.error("Deep crew execution failed: %s", e, exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "full_report_markdown": f"# Validation Failed\n\nAn error occurred during analysis: {e}",
        }

    final_report = _final_report_from_crew(crew)
    research_payload = _extract_task_payload(crew.tasks[0]) if len(crew.tasks) > 0 else {}
    analysis_payload = _extract_task_payload(crew.tasks[1]) if len(crew.tasks) > 1 else {}
    source_register = _collect_source_register(research_payload)
    research_methodology = _extract_research_methodology(research_payload)
    analysis_summary = _extract_analysis_summary(analysis_payload)

    return {
        "status": "success",
        "full_report_markdown": final_report,
        "analysis_summary": analysis_summary,
        "research_methodology": research_methodology,
        "source_register": source_register,
        "execution_metadata": {
            "tasks_completed": len(crew.tasks),
            "agents_used": len(crew.agents),
            "anthropic_model": model_used,
            "source_count": len(source_register),
        },
    }


async def run_refinement_crew(
    previous_report: str,
    user_feedback: str,
    feedback_tone: str,
    anthropic_api_key: str,
    anthropic_model: str = DEFAULT_ANTHROPIC_MODEL,
) -> str:
    """Run the refinement crew and return the revised markdown report."""
    async def _build(model_name: str) -> Crew:
        return create_refinement_crew(
            previous_report=previous_report,
            user_feedback=user_feedback,
            feedback_tone=feedback_tone,
            anthropic_api_key=anthropic_api_key,
            anthropic_model=model_name,
        )

    crew = await _kickoff_with_fallbacks(_build, anthropic_model)
    return _final_report_from_crew(crew)


async def _kickoff_with_fallbacks(
    build_crew,
    requested_model: str,
    *,
    return_model: bool = False,
):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    last_error: Exception | None = None
    for model_name in _candidate_anthropic_models(requested_model):
        try:
            crew = await build_crew(model_name)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, crew.kickoff)
            if return_model:
                return crew, model_name
            return crew
        except Exception as e:
            last_error = e
            if _is_model_not_found_error(e):
                logger.warning(
                    "Anthropic model %s is not available for this API key/runtime: %s",
                    model_name,
                    e,
                )
                continue
            raise
    if last_error is not None:
        raise last_error
    raise RuntimeError("No Anthropic model candidates configured")


def _final_report_from_crew(crew: Crew) -> str:
    last_task = crew.tasks[-1] if crew.tasks else None
    output = getattr(last_task, "output", None) if last_task else None
    for candidate in (
        getattr(output, "raw", None),
        getattr(output, "final_output", None),
        output,
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _format_answers_block(answers: Dict[str, Any]) -> str:
    if not answers:
        return "- (no answers provided)"
    lines: List[str] = []
    for key, value in answers.items():
        if value in (None, "", [], {}):
            continue
        pretty_key = str(key).replace("_", " ").title()
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        lines.append(f"- **{pretty_key}**: {value}")
    return "\n".join(lines) if lines else "- (no answers provided)"


def _normalize_anthropic_model_name(model_name: str) -> str:
    normalized = (model_name or DEFAULT_ANTHROPIC_MODEL).strip()
    if normalized.startswith("anthropic/"):
        return normalized
    return f"anthropic/{normalized}"


def _candidate_anthropic_models(requested_model: str) -> List[str]:
    candidates: List[str] = []
    for model_name in [requested_model, DEFAULT_ANTHROPIC_MODEL, *ANTHROPIC_MODEL_FALLBACKS]:
        normalized = (model_name or "").strip()
        if normalized and normalized not in candidates:
            candidates.append(normalized)
    return candidates


def _is_model_not_found_error(error: Exception) -> bool:
    message = str(error)
    return "not_found_error" in message or "Error code: 404" in message


def _extract_task_payload(task: Any) -> Dict[str, Any]:
    output = getattr(task, "output", None)
    for candidate in (
        getattr(output, "json_dict", None),
        getattr(output, "pydantic", None),
        getattr(output, "raw", None),
        output,
    ):
        payload = _coerce_to_mapping(candidate)
        if payload:
            return payload
    return {}


def _coerce_to_mapping(candidate: Any) -> Dict[str, Any]:
    if candidate is None:
        return {}
    if isinstance(candidate, dict):
        return candidate
    if hasattr(candidate, "model_dump"):
        dumped = candidate.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if isinstance(candidate, str):
        return _parse_json_like(candidate)
    return _parse_json_like(str(candidate))


def _parse_json_like(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    if not cleaned:
        return {}
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    for raw_candidate in (cleaned, _extract_braced_payload(cleaned)):
        if not raw_candidate:
            continue
        try:
            payload = json.loads(raw_candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _extract_braced_payload(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def _extract_research_methodology(research_payload: Dict[str, Any]) -> Dict[str, Any]:
    methodology_block = research_payload.get("methodology") or {}
    tools_used: List[str] = []
    explicit_tools = methodology_block.get("tools_used") if isinstance(methodology_block, dict) else None
    if isinstance(explicit_tools, list):
        tools_used.extend(str(tool) for tool in explicit_tools if tool)
    if research_payload.get("trends_analysis") or research_payload.get("overall_trend"):
        tools_used.append("Google Trends")
    if research_payload.get("competitor_intelligence") or research_payload.get("market_size_signals"):
        tools_used.append("Web Search")
    if research_payload.get("news_intelligence"):
        tools_used.append("News Intelligence")
    if research_payload.get("github_ecosystem"):
        tools_used.append("GitHub Ecosystem Analyzer")
    if research_payload.get("similarweb_signal") or research_payload.get("similarweb_competitor_signal"):
        tools_used.append("Similarweb Competitor Analyzer")
    if research_payload.get("youtube_signal") or research_payload.get("youtube_market_signal"):
        tools_used.append("YouTube Market Signal")
    if research_payload.get("website_analysis"):
        tools_used.append("Website Scraper")
    if research_payload.get("pitch_deck_analysis"):
        tools_used.append("Pitch Deck Analyzer")

    deduped_tools: List[str] = []
    for tool_name in tools_used:
        if tool_name and tool_name not in deduped_tools:
            deduped_tools.append(tool_name)

    limitations = research_payload.get("research_limitations", [])
    coverage_notes = []
    if isinstance(methodology_block, dict):
        if isinstance(methodology_block.get("research_limitations"), list):
            limitations = methodology_block.get("research_limitations")
        elif isinstance(methodology_block.get("limitations"), list):
            limitations = methodology_block.get("limitations")
        if isinstance(methodology_block.get("coverage_notes"), list):
            coverage_notes = methodology_block.get("coverage_notes")

    return {
        "tools_used": deduped_tools,
        "data_quality": research_payload.get("data_quality") or methodology_block.get("data_quality"),
        "limitations": limitations,
        "coverage_notes": coverage_notes,
    }


def _extract_analysis_summary(analysis_payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key in ("verdict", "viability_score", "confidence", "go_no_go"):
        value = analysis_payload.get(key)
        if value not in (None, "", []):
            summary[key] = value
    return summary


def _collect_source_register(research_payload: Dict[str, Any]) -> List[Dict[str, str]]:
    collected: List[Dict[str, str]] = []
    seen: set[str] = set()

    def add_source(source: Dict[str, Any]) -> None:
        title = str(source.get("title") or source.get("name") or source.get("query") or "Untitled source").strip()
        url = str(source.get("url") or source.get("link") or "").strip()
        source_type = str(source.get("source_type") or source.get("tool") or source.get("type") or "research").strip()
        insight = str(source.get("insight") or source.get("snippet") or source.get("reason") or "").strip()
        key = f"{url}|{title}"
        if not title or key in seen:
            return
        seen.add(key)
        collected.append(
            {
                "title": title,
                "url": url,
                "source_type": source_type,
                "insight": insight,
            }
        )

    explicit_sources = research_payload.get("sources") or research_payload.get("source_register") or []
    if isinstance(explicit_sources, list):
        for source in explicit_sources:
            if isinstance(source, dict):
                add_source(source)

    trends = research_payload.get("trends_analysis")
    if isinstance(trends, dict):
        add_source(
            {
                "title": "Google Trends keyword analysis",
                "url": "https://trends.google.com/",
                "source_type": "google_trends",
                "insight": trends.get("overall_direction") or research_payload.get("overall_trend", ""),
            }
        )

    for source in _walk_nested_sources(research_payload):
        add_source(source)

    return collected[:12]


def _walk_nested_sources(value: Any) -> List[Dict[str, Any]]:
    discovered: List[Dict[str, Any]] = []
    if isinstance(value, dict):
        url = value.get("url") or value.get("link")
        if url:
            discovered.append(
                {
                    "title": value.get("title") or value.get("name") or value.get("query") or url,
                    "url": url,
                    "source_type": value.get("source_type") or value.get("tool") or "research",
                    "insight": value.get("snippet") or value.get("content_preview") or value.get("sentiment") or "",
                }
            )
        for nested in value.values():
            discovered.extend(_walk_nested_sources(nested))
    elif isinstance(value, list):
        for item in value:
            discovered.extend(_walk_nested_sources(item))
    return discovered
