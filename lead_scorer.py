"""Lead Scoring Module for PRESTYJ Lead Scraper.

Scores leads 0-100 based on multiple signals.
"""

from typing import Any, Dict


def _get_rating_score(rating: float) -> float:
    """Calculate rating score (max 25 points).

    4.5+ = 25, 4.0-4.4 = 20, 3.5-3.9 = 15, <3.5 = 5
    """
    if rating >= 4.5:
        return 25
    elif rating >= 4.0:
        return 20
    elif rating >= 3.5:
        return 15
    elif rating > 0:
        return 5
    return 0


def _get_review_score(review_count: int) -> float:
    """Calculate review volume score (max 20 points).

    100+ = 20, 50-99 = 15, 10-49 = 10, 1-9 = 5
    """
    if review_count >= 100:
        return 20
    elif review_count >= 50:
        return 15
    elif review_count >= 10:
        return 10
    elif review_count >= 1:
        return 5
    return 0


def _count_social_links(lead: Dict[str, Any]) -> float:
    """Count social media platforms and return score (max 20 points).

    Each platform = 3.33 points (6 platforms max for ~20 points).
    """
    social_platforms = [
        "LinkedIn", "Facebook", "Twitter", "Instagram", "YouTube", "TikTok"
    ]
    count = 0
    for platform in social_platforms:
        if lead.get(platform):
            count += 1
    return min(count * 3.33, 20)


def _get_status_score(status: str) -> float:
    """Calculate business status score (max 10 points).

    OPERATIONAL = 10, else = 0
    """
    if status and "OPERATIONAL" in status.upper():
        return 10
    return 0


def _get_category_score(lead: Dict[str, Any]) -> float:
    """Calculate category relevance score (max 10 points).

    For now, this is a heuristic based on the business category.
    Can be overridden manually in the future.
    """
    # Check if the lead has a website (already counted separately, but this is for category-specific scoring)
    # For now, give a baseline score for having valid data
    score = 5  # Base score for having a category

    category = lead.get("Category", "").lower()

    # Higher score for service-based businesses (typically better leads)
    service_keywords = [
        "plumber", "contractor", "dentist", "doctor", "lawyer", "accountant",
        "consultant", "electrician", "roofing", "hvac", "landscaping", "cleaning"
    ]
    if any(keyword in category for keyword in service_keywords):
        score += 5

    return min(score, 10)


def calculate_lead_score(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Score a lead 0-100 based on multiple signals.

    Scoring breakdown (max 100):
    - Rating strength (25 points): 4.5+ = 25, 4.0-4.4 = 20, 3.5-3.9 = 15, <3.5 = 5
    - Review volume (20 points): 100+ = 20, 50-99 = 15, 10-49 = 10, 1-9 = 5
    - Website presence (15 points): Has website = 15, No website = 0
    - Social media presence (20 points): Each platform = 3.3 points (6 platforms max)
    - Business status (10 points): OPERATIONAL = 10, else = 0
    - Category relevance (10 points): Manual override or heuristic

    Args:
        lead: dict with keys like 'Rating', 'Reviews', 'Website', 'Status', etc.

    Returns:
        dict: {'score': int, 'breakdown': {...}}
    """
    rating = lead.get("Rating", 0) or 0
    reviews = lead.get("Reviews", 0) or 0

    breakdown = {
        "rating_score": _get_rating_score(float(rating)),
        "review_score": _get_review_score(int(reviews)),
        "website_score": 15 if lead.get("Website") else 0,
        "social_score": _count_social_links(lead),
        "status_score": _get_status_score(lead.get("Status", "")),
        "category_score": _get_category_score(lead),
    }

    total_score = sum(breakdown.values())

    return {
        "score": round(total_score),
        "breakdown": {
            "Rating": breakdown["rating_score"],
            "Reviews": breakdown["review_score"],
            "Website": breakdown["website_score"],
            "Social Media": breakdown["social_score"],
            "Status": breakdown["status_score"],
            "Category": breakdown["category_score"],
        }
    }


def get_score_emoji(score: int) -> str:
    """Get color-coded emoji for lead score."""
    if score >= 71:
        return "🟢"
    elif score >= 41:
        return "🟡"
    else:
        return "🔴"


def get_quality_label(score: int) -> str:
    """Get quality label for lead score."""
    if score >= 71:
        return "High"
    elif score >= 41:
        return "Medium"
    else:
        return "Low"
