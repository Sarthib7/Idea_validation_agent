"""VC evaluation frameworks (Sequoia, YC, Moat Analysis)"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def apply_sequoia_framework() -> Dict[str, str]:
    """
    Return the Sequoia 10-point framework structure.

    This provides the evaluation template for the VC Analyst agent.
    Based on: https://sequoiacap.com/article/writing-a-business-plan/

    Returns:
        Dict with the 10 points and evaluation questions
    """
    return {
        "framework": "Sequoia 10-Point Business Plan Evaluation",
        "points": {
            "1_company_purpose": {
                "question": "What is the company's purpose? What problem does it solve?",
                "evaluate": [
                    "Is the problem clearly defined?",
                    "Is it a real, painful problem?",
                    "Who experiences this problem?"
                ]
            },
            "2_problem": {
                "question": "What specific problem are you solving?",
                "evaluate": [
                    "How severe is the problem?",
                    "What's the current workaround?",
                    "Why hasn't it been solved yet?"
                ]
            },
            "3_solution": {
                "question": "What is your solution?",
                "evaluate": [
                    "How does the solution work?",
                    "Why is it better than alternatives?",
                    "Is it technically feasible?",
                    "Is it defensible?"
                ]
            },
            "4_why_now": {
                "question": "Why now? What's changed that makes this possible/necessary?",
                "evaluate": [
                    "Recent technology enabler?",
                    "Regulatory change?",
                    "Behavioral shift?",
                    "Market timing?"
                ]
            },
            "5_market_potential": {
                "question": "How big is the market opportunity?",
                "evaluate": [
                    "TAM/SAM/SOM estimates",
                    "Market growth rate",
                    "Is it venture-scale (>$1B potential)?"
                ]
            },
            "6_competition": {
                "question": "Who are the competitors and alternatives?",
                "evaluate": [
                    "Direct competitors",
                    "Indirect alternatives (status quo)",
                    "What's your competitive advantage?",
                    "Why won't incumbents kill you?"
                ]
            },
            "7_business_model": {
                "question": "How will you make money?",
                "evaluate": [
                    "Revenue model clarity",
                    "Unit economics (CAC, LTV, payback)",
                    "Path to profitability",
                    "Scalability of model"
                ]
            },
            "8_team": {
                "question": "Why is this team uniquely suited to win?",
                "evaluate": [
                    "Domain expertise",
                    "Prior startup experience",
                    "Technical capability",
                    "Founder-market fit",
                    "Complementary skills"
                ]
            },
            "9_financials": {
                "question": "What are the key financial metrics and projections?",
                "evaluate": [
                    "Current burn rate",
                    "Revenue trajectory",
                    "Path to next milestone",
                    "Capital efficiency"
                ]
            },
            "10_vision": {
                "question": "What's the long-term vision?",
                "evaluate": [
                    "Where will the company be in 5-10 years?",
                    "What's the ultimate outcome?",
                    "Is it an ambitious, defensible end-state?"
                ]
            }
        }
    }


def apply_yc_framework() -> Dict[str, Any]:
    """
    Return the Y Combinator 5-question filter.

    Based on YC's application evaluation criteria.

    Returns:
        Dict with the 5 core questions YC asks
    """
    return {
        "framework": "Y Combinator 5-Question Filter",
        "questions": {
            "1_interesting": {
                "question": "Is this idea interesting?",
                "evaluate": [
                    "Novel approach or unique insight?",
                    "Non-obvious solution?",
                    "Would this make you say 'wow, I want that'?"
                ]
            },
            "2_impressive_founders": {
                "question": "Are the founders impressive?",
                "evaluate": [
                    "Evidence of resourcefulness and determination",
                    "Past accomplishments",
                    "Ability to execute",
                    "Communication skills"
                ]
            },
            "3_clear_explanation": {
                "question": "Can they explain it clearly in one sentence?",
                "evaluate": [
                    "Is the value proposition simple and clear?",
                    "Can anyone understand what the company does?",
                    "No jargon or buzzwords needed?"
                ]
            },
            "4_meaningful_progress": {
                "question": "Have they made meaningful progress?",
                "evaluate": [
                    "Launched product or prototype?",
                    "Have users/customers?",
                    "Evidence of traction?",
                    "Demonstrated ability to ship?"
                ]
            },
            "5_venture_scale": {
                "question": "Is it venture-scale (potential for $100M+ revenue)?",
                "evaluate": [
                    "Market size sufficient?",
                    "Scalable business model?",
                    "Can it be a billion-dollar company?",
                    "Network effects or other growth accelerators?"
                ]
            }
        },
        "passing_score": "Strong yes on 3+ questions, no dealbreakers"
    }


def analyze_moat() -> Dict[str, Any]:
    """
    Return moat analysis framework (competitive defensibility).

    Seven types of moats that create sustainable competitive advantages.

    Returns:
        Dict with moat categories and evaluation criteria
    """
    return {
        "framework": "Competitive Moat Analysis",
        "moat_types": {
            "network_effects": {
                "description": "Product becomes more valuable as more people use it",
                "examples": "Marketplaces, social platforms, communication tools",
                "evaluate": [
                    "Does the product improve with scale?",
                    "Are there cross-side or same-side network effects?",
                    "How strong is the lock-in?"
                ],
                "strength_indicators": [
                    "Multi-player dynamics",
                    "User-generated content",
                    "Marketplace liquidity"
                ]
            },
            "switching_costs": {
                "description": "High cost or friction to switch to competitor",
                "examples": "Enterprise software, integrated systems, data lock-in",
                "evaluate": [
                    "How painful is it to switch?",
                    "Data migration complexity?",
                    "Integration dependencies?",
                    "Workflow embedding?"
                ],
                "strength_indicators": [
                    "Multi-year contracts",
                    "Deep integration",
                    "Training investment"
                ]
            },
            "proprietary_data": {
                "description": "Unique dataset that improves the product",
                "examples": "ML models, recommendation engines, market intelligence",
                "evaluate": [
                    "Is data proprietary and hard to replicate?",
                    "Does more data create better experience?",
                    "Is there a data flywheel?"
                ],
                "strength_indicators": [
                    "Exclusive data sources",
                    "Data compounding over time",
                    "Unique insights"
                ]
            },
            "brand": {
                "description": "Strong brand that customers trust and prefer",
                "examples": "Consumer brands, status symbols, quality association",
                "evaluate": [
                    "Would customers pay premium for your brand?",
                    "Word-of-mouth strength?",
                    "Category leadership?"
                ],
                "strength_indicators": [
                    "Top-of-mind awareness",
                    "Emotional connection",
                    "Cultural presence"
                ]
            },
            "economies_of_scale": {
                "description": "Unit costs decrease as scale increases",
                "examples": "Manufacturing, logistics, cloud infrastructure",
                "evaluate": [
                    "Do costs decrease with volume?",
                    "Is there a minimum efficient scale?",
                    "Can you achieve scale faster than competitors?"
                ],
                "strength_indicators": [
                    "Fixed cost leverage",
                    "Bulk purchasing power",
                    "Operational efficiency"
                ]
            },
            "regulatory_barriers": {
                "description": "Licenses, approvals, or compliance requirements limit competition",
                "examples": "Healthcare, finance, professional services",
                "evaluate": [
                    "Are there regulatory hurdles?",
                    "How long to get necessary approvals?",
                    "Can this be a moat or a risk?"
                ],
                "strength_indicators": [
                    "Required certifications",
                    "Government contracts",
                    "Compliance expertise"
                ]
            },
            "proprietary_technology": {
                "description": "Patents, trade secrets, or technical complexity",
                "examples": "Deep tech, biotech, complex algorithms",
                "evaluate": [
                    "Is technology truly unique?",
                    "Patent protection?",
                    "Time to replicate?",
                    "Required expertise level?"
                ],
                "strength_indicators": [
                    "Granted patents",
                    "Technical publications",
                    "Specialized expertise"
                ]
            }
        },
        "scoring": {
            "none": "No identifiable moat - commodity business",
            "weak": "1 weak moat - easily replicable",
            "moderate": "1-2 moderate moats - some defensibility",
            "strong": "2+ strong moats - highly defensible",
            "dominant": "Multiple compounding moats - near-monopoly"
        }
    }


def evaluate_unit_economics(
    business_model: str,
    target_audience: str,
    existing_traction: str = ""
) -> Dict[str, Any]:
    """
    Provide unit economics evaluation framework.

    Args:
        business_model: The revenue model
        target_audience: B2B or B2C focus
        existing_traction: Any traction data provided

    Returns:
        Framework for evaluating CAC, LTV, and related metrics
    """

    # Benchmark ranges by model and audience type
    benchmarks = {
        "B2B SaaS": {
            "ltv_cac_ratio": "3:1 to 5:1 (healthy)",
            "cac_payback": "12-18 months (acceptable)",
            "gross_margin": "70-85%",
            "churn": "<5% annual (good), <10% acceptable"
        },
        "B2C SaaS": {
            "ltv_cac_ratio": "3:1 minimum",
            "cac_payback": "6-12 months",
            "gross_margin": "60-80%",
            "churn": "5-7% monthly (acceptable)"
        },
        "Marketplace": {
            "ltv_cac_ratio": "2:1 early, 5:1+ at scale",
            "cac_payback": "Variable - burn to acquire network",
            "take_rate": "10-30% (depends on category)",
            "retention": "High retention = moat"
        },
        "Enterprise": {
            "ltv_cac_ratio": "5:1+ (long sales cycle amortized)",
            "cac_payback": "18-36 months",
            "gross_margin": "75-90%",
            "churn": "<5% annual (logo churn)"
        }
    }

    # Determine category
    is_b2b = "b2b" in target_audience.lower() or "enterprise" in target_audience.lower()
    category = None

    if is_b2b:
        if "Subscription (SaaS)" in business_model:
            category = "B2B SaaS"
        elif "Enterprise licensing" in business_model:
            category = "Enterprise"
    else:
        if "Subscription" in business_model or "Freemium" in business_model:
            category = "B2C SaaS"
        elif "Marketplace" in business_model:
            category = "Marketplace"

    benchmark = benchmarks.get(category, benchmarks["B2B SaaS"])

    return {
        "category": category or "General",
        "benchmarks": benchmark,
        "evaluation_framework": {
            "cac": {
                "definition": "Customer Acquisition Cost = (Sales + Marketing Spend) / New Customers",
                "questions": [
                    "What channels will you use?",
                    "What's the cost per lead/conversion?",
                    "Is CAC sustainable at scale?"
                ]
            },
            "ltv": {
                "definition": "Lifetime Value = (ARPU × Gross Margin) / Churn Rate",
                "questions": [
                    "What's the average revenue per user?",
                    "What's the expected customer lifetime?",
                    "How will LTV increase over time?"
                ]
            },
            "payback_period": {
                "definition": "Months to recover CAC from gross margin",
                "target": benchmark.get("cac_payback", "12 months"),
                "questions": [
                    "How quickly can you recoup acquisition cost?",
                    "Can you afford the cash burn?"
                ]
            }
        }
    }
