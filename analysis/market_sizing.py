"""TAM/SAM/SOM market sizing estimation"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def estimate_market_size(
    idea_description: str,
    industry: str,
    target_audience: str,
    business_model: str,
    research_data: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Estimate TAM/SAM/SOM for the startup idea.

    TAM (Total Addressable Market): Total market demand for the product/service
    SAM (Serviceable Addressable Market): Segment of TAM targeted by your products/services within your geographical reach
    SOM (Serviceable Obtainable Market): Portion of SAM that you can realistically capture in 3-5 years

    This is a framework helper - the actual estimation is done by the LLM agent
    using this structure + research data.

    Args:
        idea_description: The startup idea
        industry: Industry vertical
        target_audience: Target customer profile
        business_model: Revenue model
        research_data: Optional research findings from tools

    Returns:
        Dict with estimation framework and guidance
    """

    # Industry-specific TAM references (these are rough guides for the LLM)
    industry_tam_guides = {
        "SaaS / Software": {
            "global_software_market": "$650B+ (2024)",
            "growth_rate": "10-15% CAGR",
            "note": "Highly fragmented, focus on specific vertical"
        },
        "AI / Machine Learning": {
            "global_ai_market": "$200B+ (2024)",
            "growth_rate": "35-40% CAGR",
            "note": "Rapidly growing, but competitive"
        },
        "Fintech / Payments": {
            "global_fintech_market": "$300B+ (2024)",
            "growth_rate": "20-25% CAGR",
            "note": "Regulatory considerations impact SAM"
        },
        "Healthcare / Biotech": {
            "global_healthtech_market": "$250B+ (2024)",
            "growth_rate": "15-20% CAGR",
            "note": "Long sales cycles, regulatory approval needed"
        },
        "E-commerce / Marketplace": {
            "global_ecommerce_market": "$5T+ (2024)",
            "growth_rate": "10-12% CAGR",
            "note": "Winner-take-most dynamics"
        },
        "Web3 / Blockchain": {
            "global_web3_market": "$50B+ (2024)",
            "growth_rate": "40-50% CAGR (volatile)",
            "note": "Emerging market, high uncertainty"
        }
    }

    industry_guide = industry_tam_guides.get(industry, {
        "note": "Use comparable company analysis and bottom-up estimation"
    })

    # Business model impacts on SOM (realistic capture rates)
    som_guidance = {
        "Subscription (SaaS)": {
            "typical_som": "2-5% of SAM in 5 years",
            "note": "Depends on CAC, churn, and competitive moat"
        },
        "Marketplace / Commission": {
            "typical_som": "0.5-3% of SAM in 5 years",
            "note": "Network effects can accelerate growth after critical mass"
        },
        "Freemium": {
            "typical_som": "1-4% of SAM in 5 years",
            "note": "Conversion rate typically 2-5%"
        },
        "Enterprise licensing": {
            "typical_som": "3-7% of SAM in 5 years",
            "note": "Higher capture rate but slower growth"
        }
    }

    model_guidance = som_guidance.get(business_model, {
        "typical_som": "2-5% of SAM in 5 years",
        "note": "Standard startup capture rate"
    })

    return {
        "framework": "TAM/SAM/SOM Analysis",
        "tam_guidance": industry_guide,
        "sam_considerations": [
            "Geographic constraints (starting region)",
            "Segment focus (B2B vs B2C, company size, demographics)",
            "Product limitations (features, integrations)",
            "Regulatory barriers",
            "Competitive positioning"
        ],
        "som_guidance": model_guidance,
        "calculation_approach": "Bottom-up: (# potential customers) × (average deal size) × (market penetration %)",
        "validation_sources": [
            "Public market research reports",
            "Competitor revenue data (if available)",
            "Industry analyst estimates",
            "Addressable customer count × willingness to pay"
        ]
    }


def validate_market_size_estimates(tam: str, sam: str, som: str) -> Dict[str, Any]:
    """
    Validate that market size estimates follow logical constraints.

    Args:
        tam: TAM estimate string (e.g., "$10B")
        sam: SAM estimate string (e.g., "$2B")
        som: SOM estimate string (e.g., "$100M")

    Returns:
        Validation result with warnings
    """
    try:
        # Extract numeric values (very basic - assumes format like "$10B")
        def extract_value(s: str) -> float:
            s = s.upper().replace('$', '').replace(',', '').strip()
            multiplier = 1
            if 'B' in s:
                multiplier = 1_000_000_000
                s = s.replace('B', '')
            elif 'M' in s:
                multiplier = 1_000_000
                s = s.replace('M', '')
            elif 'K' in s:
                multiplier = 1_000
                s = s.replace('K', '')

            return float(s) * multiplier

        tam_val = extract_value(tam)
        sam_val = extract_value(sam)
        som_val = extract_value(som)

        warnings = []

        # SAM should be <= TAM
        if sam_val > tam_val:
            warnings.append("SAM exceeds TAM - this is logically incorrect")

        # SOM should be <= SAM
        if som_val > sam_val:
            warnings.append("SOM exceeds SAM - this is logically incorrect")

        # SOM should typically be 2-10% of SAM for early-stage startups
        som_percentage = (som_val / sam_val * 100) if sam_val > 0 else 0
        if som_percentage > 15:
            warnings.append(f"SOM is {som_percentage:.1f}% of SAM - unusually high for a startup (typically 2-10%)")
        elif som_percentage < 0.5:
            warnings.append(f"SOM is {som_percentage:.1f}% of SAM - may be too conservative")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "som_as_percent_of_sam": round(som_percentage, 2)
        }

    except Exception as e:
        logger.warning(f"Could not validate market size estimates: {e}")
        return {
            "valid": True,
            "warnings": ["Could not validate - ensure format is like '$10B', '$500M', etc."]
        }
