"""Output schema for validation reports"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Verdict(str, Enum):
    """Overall verdict categories"""
    STRONG_OPPORTUNITY = "STRONG OPPORTUNITY"
    PROMISING = "PROMISING"
    NEEDS_WORK = "NEEDS WORK"
    HIGH_RISK = "HIGH RISK"
    DO_NOT_PURSUE = "DO NOT PURSUE"


class Confidence(str, Enum):
    """Confidence level in the verdict"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TrendDirection(str, Enum):
    """Market trend direction"""
    GROWING = "GROWING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScoreDimension(BaseModel):
    """Individual scoring dimension"""
    score: int = Field(ge=1, le=10, description="Score from 1-10")
    reason: str = Field(description="Explanation for the score")


class MarketAnalysis(BaseModel):
    """Market analysis results"""
    tam_estimate: str = Field(description="Total Addressable Market estimate")
    sam_estimate: str = Field(description="Serviceable Addressable Market estimate")
    som_estimate: str = Field(description="Serviceable Obtainable Market estimate")
    trend_direction: TrendDirection
    google_trends_summary: Optional[str] = None
    external_research_summary: Optional[str] = None
    key_competitors: List[str] = Field(default_factory=list)
    market_gaps_identified: List[str] = Field(default_factory=list)


class CriticalRisk(BaseModel):
    """Critical risk item"""
    risk: str = Field(description="Description of the risk")
    severity: RiskSeverity
    mitigation: str = Field(description="Suggested mitigation strategy")


class ActionableStep(BaseModel):
    """Actionable next step"""
    priority: int = Field(ge=1, description="Priority order (1 = highest)")
    action: str = Field(description="What to do")
    timeline: str = Field(description="Suggested timeline")


class ValidationReport(BaseModel):
    """Complete validation report structure"""
    verdict: Verdict
    viability_score: int = Field(ge=0, le=100, description="Overall viability score 0-100")
    confidence: Confidence
    go_no_go: str = Field(description="Go/No-Go recommendation with reasoning")

    # Scoring matrix (10 dimensions)
    scoring_matrix: Dict[str, ScoreDimension] = Field(
        description="10-dimension scoring matrix with explanations"
    )

    executive_summary: str = Field(description="2-3 paragraph investment thesis")

    market_analysis: MarketAnalysis

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)

    critical_risks: List[CriticalRisk] = Field(default_factory=list)
    actionable_next_steps: List[ActionableStep] = Field(default_factory=list)

    pitch_deck_feedback: Optional[str] = Field(
        default=None,
        description="Feedback on pitch deck if file was provided"
    )
    website_feedback: Optional[str] = Field(
        default=None,
        description="Feedback on website if URL was provided"
    )

    full_report_markdown: str = Field(
        description="Complete formatted report with tone applied"
    )

    class Config:
        use_enum_values = True


def calculate_viability_score(scoring_matrix: Dict[str, ScoreDimension]) -> int:
    """
    Calculate overall viability score from the 10-dimension matrix.

    Weights:
    - Market Opportunity: 15%
    - Problem Severity: 10%
    - Solution Quality: 10%
    - Timing (Why Now): 10%
    - Competitive Advantage: 15%
    - Business Model Viability: 10%
    - Team Readiness: 10%
    - Scalability Potential: 10%
    - Risk Assessment: 5%
    - Investment Potential: 5%

    Args:
        scoring_matrix: Dictionary of dimension scores

    Returns:
        Overall viability score (0-100)
    """
    weights = {
        "market_opportunity": 0.15,
        "problem_severity": 0.10,
        "solution_quality": 0.10,
        "timing_why_now": 0.10,
        "competitive_advantage": 0.15,
        "business_model_viability": 0.10,
        "team_readiness": 0.10,
        "scalability_potential": 0.10,
        "risk_assessment": 0.05,
        "investment_potential": 0.05
    }

    weighted_sum = 0.0
    for dimension, weight in weights.items():
        if dimension in scoring_matrix:
            weighted_sum += scoring_matrix[dimension].score * weight * 10

    return int(weighted_sum)


def determine_verdict(viability_score: int) -> Verdict:
    """
    Determine verdict based on viability score.

    Score ranges:
    - 80-100: STRONG OPPORTUNITY
    - 65-79: PROMISING
    - 50-64: NEEDS WORK
    - 35-49: HIGH RISK
    - 0-34: DO NOT PURSUE

    Args:
        viability_score: Overall viability score

    Returns:
        Verdict enum
    """
    if viability_score >= 80:
        return Verdict.STRONG_OPPORTUNITY
    elif viability_score >= 65:
        return Verdict.PROMISING
    elif viability_score >= 50:
        return Verdict.NEEDS_WORK
    elif viability_score >= 35:
        return Verdict.HIGH_RISK
    else:
        return Verdict.DO_NOT_PURSUE
