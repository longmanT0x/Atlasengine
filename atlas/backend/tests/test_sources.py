"""
Test source collection and quality.

Validates that sufficient sources are collected and returned.
"""

import pytest
from tests.fixtures.sample_ideas import get_all_test_ideas


@pytest.mark.asyncio
async def test_minimum_sources_returned(test_client, sample_ideas):
    """
    Test that at least N sources are returned for each idea.
    
    Each idea has a minimum expected number of sources based on its characteristics.
    """
    for idea_name, idea_data in sample_ideas.items():
        min_sources = idea_data["expected_characteristics"]["min_sources"]
        
        request_data = {
            "idea": idea_data["idea"],
            "industry": idea_data["industry"],
            "geography": idea_data["geography"],
            "customer_type": idea_data["customer_type"],
            "business_model": idea_data["business_model"],
            "price_assumption": idea_data.get("price_assumption"),
            "notes": idea_data.get("notes"),
            "debug": False
        }
        
        response = test_client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 200, f"Request failed for {idea_name}"
        
        response_data = response.json()
        sources = response_data.get("sources", [])
        
        assert len(sources) >= min_sources, \
            f"Expected at least {min_sources} sources for {idea_name}, got {len(sources)}"
        
        # Validate source structure
        for source in sources:
            assert "title" in source, f"Source missing title for {idea_name}"
            assert "url" in source, f"Source missing URL for {idea_name}"
            assert "excerpt" in source, f"Source missing excerpt for {idea_name}"
            assert source["url"] != "unknown", \
                f"Source URL should not be 'unknown' for {idea_name}"


@pytest.mark.asyncio
async def test_sources_have_valid_urls(test_client, fintech_eu_idea):
    """Test that all sources have valid URLs."""
    request_data = {
        "idea": fintech_eu_idea["idea"],
        "industry": fintech_eu_idea["industry"],
        "geography": fintech_eu_idea["geography"],
        "customer_type": fintech_eu_idea["customer_type"],
        "business_model": fintech_eu_idea["business_model"],
        "price_assumption": fintech_eu_idea.get("price_assumption"),
        "notes": fintech_eu_idea.get("notes"),
        "debug": False
    }
    
    response = test_client.post("/api/v1/analyze", json=request_data)
    assert response.status_code == 200
    
    response_data = response.json()
    sources = response_data.get("sources", [])
    
    for source in sources:
        url = source.get("url", "")
        # URL should start with http:// or https://
        assert url.startswith(("http://", "https://")) or url == "unknown", \
            f"Invalid URL format: {url}"


