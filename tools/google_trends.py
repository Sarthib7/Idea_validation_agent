"""Google Trends research tool"""
import logging
from typing import Dict, Any, Optional, List
from crewai.tools import tool
from pytrends.request import TrendReq
import time

logger = logging.getLogger(__name__)


@tool("Google Trends Analyzer")
def google_trends_tool(keywords: str) -> str:
    """
    Analyze Google Trends data for given keywords.

    Args:
        keywords: Comma-separated keywords to analyze (max 5)

    Returns:
        JSON string with trend analysis including interest over time,
        related queries, and breakout signals
    """
    try:
        # Parse keywords
        keyword_list = [k.strip() for k in keywords.split(",")][:5]

        if not keyword_list:
            return '{"error": "No keywords provided"}'

        logger.info(f"Analyzing Google Trends for: {keyword_list}")

        # Initialize pytrends
        pytrends = TrendReq(hl='en-US', tz=360)

        # Build payload
        pytrends.build_payload(
            keyword_list,
            cat=0,
            timeframe='today 12-m',
            geo='',
            gprop=''
        )

        result = {
            "keywords": keyword_list,
            "analysis": {}
        }

        # Get interest over time
        try:
            interest_over_time_df = pytrends.interest_over_time()
            if not interest_over_time_df.empty:
                # Calculate trend direction for each keyword
                for keyword in keyword_list:
                    if keyword in interest_over_time_df.columns:
                        values = interest_over_time_df[keyword].values
                        # Simple trend: compare last 3 months avg to first 3 months avg
                        if len(values) >= 6:
                            early_avg = values[:3].mean()
                            recent_avg = values[-3:].mean()

                            if recent_avg > early_avg * 1.2:
                                direction = "GROWING"
                            elif recent_avg < early_avg * 0.8:
                                direction = "DECLINING"
                            else:
                                direction = "STABLE"

                            result["analysis"][keyword] = {
                                "trend_direction": direction,
                                "average_interest": int(values.mean()),
                                "peak_interest": int(values.max()),
                                "current_interest": int(values[-1])
                            }
                        else:
                            result["analysis"][keyword] = {
                                "trend_direction": "INSUFFICIENT_DATA",
                                "average_interest": 0,
                                "peak_interest": 0,
                                "current_interest": 0
                            }
        except Exception as e:
            logger.warning(f"Failed to get interest over time: {e}")
            result["interest_over_time_error"] = str(e)

        # Get related queries
        time.sleep(1)  # Rate limiting
        try:
            related_queries = pytrends.related_queries()
            breakout_queries = []

            for keyword in keyword_list:
                if keyword in related_queries:
                    rising = related_queries[keyword].get('rising')
                    if rising is not None and not rising.empty:
                        # Look for "Breakout" signals
                        breakout_items = rising[rising['value'] == 'Breakout']
                        if not breakout_items.empty:
                            breakout_queries.extend(
                                breakout_items['query'].tolist()
                            )

            if breakout_queries:
                result["breakout_signals"] = breakout_queries[:10]
        except Exception as e:
            logger.warning(f"Failed to get related queries: {e}")
            result["related_queries_error"] = str(e)

        # Overall summary
        growing_count = sum(
            1 for k, v in result["analysis"].items()
            if v.get("trend_direction") == "GROWING"
        )

        if growing_count >= len(keyword_list) / 2:
            result["overall_trend"] = "GROWING"
        elif growing_count == 0:
            result["overall_trend"] = "STABLE_OR_DECLINING"
        else:
            result["overall_trend"] = "MIXED"

        import json
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Google Trends tool error: {e}")
        return f'{{"error": "{str(e)}"}}'
