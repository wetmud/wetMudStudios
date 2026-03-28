from scorer import score_lead, ScoringResult

def test_no_website_adds_40():
    result = score_lead(
        has_website=False, has_google_listing=True, site_platform=None,
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("no_website") == 40
    assert result.score >= 40

def test_no_gmb_adds_30():
    result = score_lead(
        has_website=True, has_google_listing=False, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("no_gmb") == 30

def test_template_site_adds_20():
    for platform in ("wix", "squarespace", "weebly"):
        result = score_lead(
            has_website=True, has_google_listing=True, site_platform=platform,
            review_count=20, last_review_date="2025-01-01",
            niche="restaurant", has_ssl=True, target_niches=[]
        )
        assert result.breakdown.get("template_site") == 20, "Failed for " + platform

def test_few_reviews_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=5, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("few_or_old_reviews") == 10

def test_old_reviews_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=50, last_review_date="2022-01-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.breakdown.get("few_or_old_reviews") == 10

def test_niche_match_adds_15():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=True, target_niches=["restaurant", "salon"]
    )
    assert result.breakdown.get("niche_match") == 15

def test_no_ssl_adds_10():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=20, last_review_date="2025-01-01",
        niche="restaurant", has_ssl=False, target_niches=[]
    )
    assert result.breakdown.get("no_ssl") == 10

def test_score_capped_at_100():
    result = score_lead(
        has_website=False, has_google_listing=False, site_platform="wix",
        review_count=2, last_review_date="2020-01-01",
        niche="restaurant", has_ssl=False, target_niches=["restaurant"]
    )
    assert result.score <= 100

def test_perfect_business_scores_zero():
    result = score_lead(
        has_website=True, has_google_listing=True, site_platform="custom",
        review_count=100, last_review_date="2025-12-01",
        niche="restaurant", has_ssl=True, target_niches=[]
    )
    assert result.score == 0

def test_returns_correct_types():
    result = score_lead(
        has_website=False, has_google_listing=True, site_platform=None,
        review_count=5, last_review_date=None,
        niche=None, has_ssl=False, target_niches=[]
    )
    assert isinstance(result, ScoringResult)
    assert isinstance(result.score, int)
    assert isinstance(result.breakdown, dict)
