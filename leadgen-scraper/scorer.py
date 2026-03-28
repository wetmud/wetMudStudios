from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class ScoringResult:
    score: int
    breakdown: dict

def score_lead(
    has_website: bool,
    has_google_listing: bool,
    site_platform: Optional[str],
    review_count: Optional[int],
    last_review_date: Optional[str],
    niche: Optional[str],
    has_ssl: bool,
    target_niches: list,
) -> ScoringResult:
    breakdown = {}
    total = 0

    if not has_website:
        breakdown["no_website"] = 40
        total += 40

    if not has_google_listing:
        breakdown["no_gmb"] = 30
        total += 30

    if site_platform in ("wix", "squarespace", "weebly"):
        breakdown["template_site"] = 20
        total += 20

    review_pts = 0
    if review_count is not None and review_count < 10:
        review_pts = 10
    elif last_review_date:
        try:
            last = datetime.strptime(last_review_date, "%Y-%m-%d").date()
            if (date.today() - last).days > 365:
                review_pts = 10
        except ValueError:
            pass
    if review_pts:
        breakdown["few_or_old_reviews"] = review_pts
        total += review_pts

    if niche and target_niches and niche.lower() in [n.lower() for n in target_niches]:
        breakdown["niche_match"] = 15
        total += 15

    if not has_ssl:
        breakdown["no_ssl"] = 10
        total += 10

    return ScoringResult(score=min(total, 100), breakdown=breakdown)
