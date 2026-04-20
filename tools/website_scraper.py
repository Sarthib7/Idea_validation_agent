"""Website scraping and analysis tool"""
import logging
from typing import Dict, Any
from crewai.tools import tool
import json

logger = logging.getLogger(__name__)


@tool("Website Scraper")
def website_scraper_tool(url: str) -> str:
    """
    Scrape and analyze a website URL (landing page, product site, etc).

    Args:
        url: Full URL to scrape (must include http:// or https://)

    Returns:
        JSON string with site analysis including content, structure, and positioning
    """
    try:
        import httpx
        from bs4 import BeautifulSoup

        if not url or not (url.startswith('http://') or url.startswith('https://')):
            return json.dumps({
                "error": "Invalid URL",
                "message": "URL must start with http:// or https://"
            })

        logger.info(f"Scraping website: {url}")

        # Try basic HTTP request first
        try:
            response = httpx.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            html = response.text

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Extract key elements
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title found"

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''

            # H1 headings (usually the main value proposition)
            h1_tags = soup.find_all('h1')
            h1_texts = [h.get_text().strip() for h in h1_tags[:3]]

            # H2 headings (features, benefits)
            h2_tags = soup.find_all('h2')
            h2_texts = [h.get_text().strip() for h in h2_tags[:5]]

            # Extract main paragraphs
            paragraphs = soup.find_all('p')
            main_text = ' '.join([p.get_text().strip() for p in paragraphs[:10]])[:1000]

            # Check for common startup signals
            has_pricing = bool(soup.find(string=lambda text: text and 'pricing' in text.lower()))
            has_demo = bool(soup.find(string=lambda text: text and ('demo' in text.lower() or 'try free' in text.lower())))
            has_testimonials = bool(soup.find(string=lambda text: text and 'testimonial' in text.lower()))

            result = {
                "url": url,
                "status": "success",
                "page_title": title_text,
                "meta_description": description,
                "main_headings": h1_texts,
                "subheadings": h2_texts,
                "content_preview": main_text[:500],
                "signals": {
                    "has_pricing_page": has_pricing,
                    "has_demo_or_trial": has_demo,
                    "has_testimonials": has_testimonials
                },
                "content_quality": _assess_content_quality(
                    title_text, description, h1_texts, main_text
                )
            }

            return json.dumps(result, indent=2)

        except httpx.HTTPError as e:
            # If HTTP fails, could try playwright for JS-heavy sites
            # but skipping for simplicity in initial implementation
            logger.warning(f"HTTP scraping failed for {url}: {e}")
            return json.dumps({
                "url": url,
                "status": "failed",
                "error": f"Could not fetch page: {str(e)}",
                "suggestion": "Page may require JavaScript rendering or may be inaccessible"
            })

    except ImportError as e:
        return json.dumps({
            "error": f"Missing dependency: {e}",
            "message": "Install httpx and beautifulsoup4"
        })
    except Exception as e:
        logger.error(f"Website scraper error: {e}")
        return json.dumps({"error": str(e)})


def _assess_content_quality(title: str, description: str, h1_texts: list, content: str) -> Dict[str, Any]:
    """Assess quality of website content and messaging"""

    quality = {
        "clarity_score": 0,
        "issues": [],
        "strengths": []
    }

    # Check if value proposition is clear
    if h1_texts and len(h1_texts[0]) > 10:
        quality["strengths"].append("Clear main heading present")
        quality["clarity_score"] += 3
    else:
        quality["issues"].append("Weak or missing main heading")

    # Check meta description
    if description and len(description) > 50:
        quality["strengths"].append("Good meta description")
        quality["clarity_score"] += 2
    else:
        quality["issues"].append("Missing or weak meta description")

    # Check content length
    if len(content) > 200:
        quality["strengths"].append("Sufficient content")
        quality["clarity_score"] += 2
    else:
        quality["issues"].append("Very limited content")

    # Check for buzzword overload
    buzzwords = ['revolutionary', 'disruptive', 'cutting-edge', 'innovative', 'next-generation']
    buzzword_count = sum(content.lower().count(word) for word in buzzwords)
    if buzzword_count > 5:
        quality["issues"].append("Heavy use of buzzwords - may lack substance")
    else:
        quality["clarity_score"] += 1

    # Normalize score 0-10
    quality["clarity_score"] = min(10, quality["clarity_score"])

    return quality
