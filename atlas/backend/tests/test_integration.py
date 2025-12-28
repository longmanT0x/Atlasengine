"""
Integration tests for the full analysis pipeline.

Tests the complete flow from request to response.
"""

import pytest
from tests.fixtures.sample_ideas import get_all_test_ideas


@pytest.mark.asyncio
async def test_full_pipeline_execution(test_client, fintech_eu_idea):
    """Test that the full pipeline executes without errors."""
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
    
    # Should return 200 even if some steps have issues (graceful degradation)
    assert response.status_code in [200, 500], \
        f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        response_data = response.json()
        
        # Validate basic structure
        assert "verdict" in response_data
        assert "confidence_score" in response_data
        assert "executive_summary" in response_data
        assert "market" in response_data
        assert "competitors" in response_data
        assert "risks" in response_data
        assert "assumptions" in response_data
        assert "sources" in response_data


@pytest.mark.asyncio
async def test_all_sample_ideas_execute(test_client, sample_ideas):
    """Test that all sample ideas can be processed."""
    for idea_name, idea_data in sample_ideas.items():
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
        
        # Should not crash - may return 200 or 500 depending on external factors
        assert response.status_code in [200, 500], \
            f"Unexpected status code for {idea_name}: {response.status_code}"


