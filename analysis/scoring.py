"""Scoring matrix computation for startup validation"""
import logging
from typing import Dict, Any
from schemas.output_schema import ScoreDimension, Verdict, Confidence

logger = logging.getLogger(__name__)


def compute_scoring_matrix(analysis_results: Dict[str, Any]) -> Dict[str, ScoreDimension]:
    """
    Framework for computing the 10-dimension scoring matrix.

    This provides structure - the actual scoring is done by the VC Analyst agent.

    The 10 dimensions:
    1. Market Opportunity (15% weight)
    2. Problem Severity (10% weight)
    3. Solution Quality (10% weight)
    4. Timing / Why Now (10% weight)
    5. Competitive Advantage (15% weight)
    6. Business Model Viability (10% weight)
    7. Team Readiness (10% weight)
    8. Scalability Potential (10% weight)
    9. Risk Assessment (5% weight) - inverse: lower score = higher risk
    10. Investment Potential (5% weight)

    Args:
        analysis_results: Research and framework analysis results

    Returns:
        Scoring matrix structure for the LLM to populate
    """

    scoring_dimensions = {
        "market_opportunity": {
            "weight": 0.15,
            "description": "Size and growth potential of the target market",
            "scoring_guide": {
                "9-10": "Massive market ($10B+ TAM), high growth (>20% CAGR), clear unmet need",
                "7-8": "Large market ($1-10B TAM), solid growth (10-20% CAGR)",
                "5-6": "Medium market ($100M-1B TAM) or saturated large market",
                "3-4": "Small market (<$100M TAM) or declining market",
                "1-2": "Negligible market or already dominated by incumbents"
            },
            "consider": [
                "TAM/SAM/SOM estimates",
                "Market growth rate",
                "Trend direction (Google Trends data)",
                "Industry maturity"
            ]
        },
        "problem_severity": {
            "weight": 0.10,
            "description": "How painful is the problem being solved?",
            "scoring_guide": {
                "9-10": "Critical pain point, users actively seeking solutions, high urgency",
                "7-8": "Significant problem, clear demand signals",
                "5-6": "Moderate problem, nice-to-have improvement",
                "3-4": "Minor inconvenience, low urgency",
                "1-2": "Solving a problem that doesn't really exist"
            },
            "consider": [
                "External research dossier pain-point evidence",
                "Current workarounds and their costs",
                "Willingness to pay indicators",
                "Problem frequency"
            ]
        },
        "solution_quality": {
            "weight": 0.10,
            "description": "How good is the proposed solution?",
            "scoring_guide": {
                "9-10": "Elegant, 10x better than alternatives, clear differentiation",
                "7-8": "Strong solution, meaningful improvement over status quo",
                "5-6": "Decent solution, incremental improvement",
                "3-4": "Questionable solution, unclear if better",
                "1-2": "Poor solution, doesn't solve the core problem"
            },
            "consider": [
                "Technical feasibility",
                "User experience promise",
                "Differentiation vs competitors",
                "Founder's explanation clarity"
            ]
        },
        "timing_why_now": {
            "weight": 0.10,
            "description": "Why is this the right time for this idea?",
            "scoring_guide": {
                "9-10": "Perfect timing - recent enabler + growing urgency + market shift",
                "7-8": "Good timing - clear catalysts present",
                "5-6": "Neutral timing - no strong signals either way",
                "3-4": "Poor timing - too early or too late",
                "1-2": "Wrong time - market moving opposite direction"
            },
            "consider": [
                "Technology enablers",
                "Regulatory changes",
                "Behavioral/cultural shifts",
                "Recent events creating urgency",
                "Trend direction"
            ]
        },
        "competitive_advantage": {
            "weight": 0.15,
            "description": "Strength of moats and defensibility",
            "scoring_guide": {
                "9-10": "Multiple strong moats, nearly impossible to replicate",
                "7-8": "2+ moderate moats, defensible position",
                "5-6": "1 weak moat, some differentiation",
                "3-4": "No clear moat, easily replicable",
                "1-2": "Commodity product, zero defensibility"
            },
            "consider": [
                "Moat analysis results",
                "Unique advantages claimed",
                "Competitor analysis",
                "Switching costs",
                "Network effects potential"
            ]
        },
        "business_model_viability": {
            "weight": 0.10,
            "description": "How strong is the monetization strategy?",
            "scoring_guide": {
                "9-10": "Proven model, great unit economics, clear path to profit",
                "7-8": "Solid model, reasonable economics",
                "5-6": "Workable model, needs optimization",
                "3-4": "Questionable model, unclear path to profitability",
                "1-2": "Broken model, doesn't make financial sense"
            },
            "consider": [
                "Revenue model clarity",
                "Unit economics benchmarks",
                "Scalability of model",
                "Pricing strategy",
                "Market willingness to pay"
            ]
        },
        "team_readiness": {
            "weight": 0.10,
            "description": "Is the team capable of executing?",
            "scoring_guide": {
                "9-10": "A-team, proven track record, perfect founder-market fit",
                "7-8": "Strong team, relevant experience",
                "5-6": "Decent team, some gaps",
                "3-4": "Weak team, major capability gaps",
                "1-2": "Wrong team for this problem"
            },
            "consider": [
                "Founder stage",
                "Team size and composition",
                "Domain expertise signals",
                "Prior accomplishments",
                "Complementary skills"
            ]
        },
        "scalability_potential": {
            "weight": 0.10,
            "description": "Can this scale to $100M+ revenue?",
            "scoring_guide": {
                "9-10": "Extremely scalable, low marginal costs, exponential growth potential",
                "7-8": "Highly scalable, clear path to scale",
                "5-6": "Moderately scalable, linear growth",
                "3-4": "Limited scalability, high friction",
                "1-2": "Not scalable, inherent constraints"
            },
            "consider": [
                "Business model scalability",
                "Marginal economics",
                "Distribution strategy",
                "Operational leverage",
                "Capital efficiency"
            ]
        },
        "risk_assessment": {
            "weight": 0.05,
            "description": "Overall risk level (INVERSE: lower score = higher risk)",
            "scoring_guide": {
                "9-10": "Very low risk - clear path, proven model, strong team",
                "7-8": "Manageable risks - identifiable and mitigatable",
                "5-6": "Moderate risks - requires careful execution",
                "3-4": "High risks - multiple critical uncertainties",
                "1-2": "Extreme risks - likely to fail"
            },
            "consider": [
                "Market risk",
                "Execution risk",
                "Competitive risk",
                "Regulatory risk",
                "Technology risk",
                "Team risk"
            ]
        },
        "investment_potential": {
            "weight": 0.05,
            "description": "Overall attractiveness as an investment",
            "scoring_guide": {
                "9-10": "Home run potential - could be a unicorn",
                "7-8": "Strong investment - likely solid returns",
                "5-6": "Decent opportunity - moderate returns possible",
                "3-4": "Weak investment - likely to struggle",
                "1-2": "Not investable - avoid"
            },
            "consider": [
                "Exit potential",
                "Venture scale (can reach $1B valuation?)",
                "ROI potential",
                "Time to liquidity",
                "Fundability by other VCs"
            ]
        }
    }

    return scoring_dimensions


def calculate_confidence_level(
    data_quality: str,
    assumption_count: int,
    research_completeness: float
) -> Confidence:
    """
    Determine confidence level in the verdict.

    Args:
        data_quality: Quality of research data ("high", "medium", "low")
        assumption_count: Number of major assumptions made
        research_completeness: Percentage of research successfully completed (0-1)

    Returns:
        Confidence enum (HIGH, MEDIUM, LOW)
    """

    confidence_score = 0

    # Data quality contribution (0-40 points)
    if data_quality == "high":
        confidence_score += 40
    elif data_quality == "medium":
        confidence_score += 25
    elif data_quality == "low":
        confidence_score += 10

    # Research completeness contribution (0-40 points)
    confidence_score += research_completeness * 40

    # Assumption penalty (0-20 points, inverse)
    if assumption_count == 0:
        confidence_score += 20
    elif assumption_count <= 2:
        confidence_score += 15
    elif assumption_count <= 5:
        confidence_score += 10
    else:
        confidence_score += 5

    # Determine confidence level
    if confidence_score >= 80:
        return Confidence.HIGH
    elif confidence_score >= 50:
        return Confidence.MEDIUM
    else:
        return Confidence.LOW


def generate_go_no_go_recommendation(
    verdict: Verdict,
    viability_score: int,
    critical_risks: list,
    strengths: list
) -> str:
    """
    Generate the Go/No-Go recommendation with reasoning.

    Args:
        verdict: Overall verdict enum
        viability_score: Viability score (0-100)
        critical_risks: List of critical risks
        strengths: List of key strengths

    Returns:
        Go/No-Go recommendation string with reasoning
    """

    if verdict == Verdict.STRONG_OPPORTUNITY:
        return (
            f"STRONG GO — This is a compelling opportunity with a viability score of {viability_score}/100. "
            f"Key strengths: {', '.join(strengths[:3])}. "
            f"Proceed with confidence, but monitor: {', '.join([r.risk for r in critical_risks[:2]]) if critical_risks else 'standard execution risks'}."
        )
    elif verdict == Verdict.PROMISING:
        return (
            f"CONDITIONAL GO — This shows promise (score: {viability_score}/100) but requires addressing key risks first. "
            f"Strengths: {', '.join(strengths[:2])}. "
            f"Before proceeding, mitigate: {', '.join([r.risk for r in critical_risks[:3]]) if critical_risks else 'identified weaknesses'}."
        )
    elif verdict == Verdict.NEEDS_WORK:
        return (
            f"PROCEED WITH CAUTION — The idea needs significant work (score: {viability_score}/100). "
            f"Critical improvements needed: {', '.join([r.risk for r in critical_risks[:3]]) if critical_risks else 'multiple dimensions'}. "
            f"Consider pivoting or addressing fundamental issues before investing heavily."
        )
    elif verdict == Verdict.HIGH_RISK:
        return (
            f"WEAK NO — High risk of failure (score: {viability_score}/100). "
            f"Major concerns: {', '.join([r.risk for r in critical_risks[:3]]) if critical_risks else 'fundamental viability issues'}. "
            f"Only proceed if you can fundamentally change these aspects."
        )
    else:  # DO_NOT_PURSUE
        return (
            f"STRONG NO — Do not pursue this idea (score: {viability_score}/100). "
            f"Fatal flaws: {', '.join([r.risk for r in critical_risks[:3]]) if critical_risks else 'non-viable on multiple dimensions'}. "
            f"Recommend pivoting to a different opportunity."
        )
