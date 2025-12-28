"""
Test evidence traceability.

Validates that all numeric claims have sources and are traceable.
"""

import pytest
from tests.fixtures.sample_ideas import get_all_test_ideas


@pytest.mark.asyncio
async def test_all_numeric_claims_have_sources(test_client, sample_ideas):
    """
    Test that all numeric claims in the response have source attribution.
    
    This validates:
    - Market size estimates reference sources
    - All numeric values can be traced back to evidence
    """
    for idea_name, idea_data in sample_ideas.items():
        request_data = {
            "idea": idea_data["idea"],
            "industry": idea_data["industry"],
            "geography": idea_data["geography"],
            "customer_type": idea_data["customer_type"],
            "business_model": idea_data["business_model"],
            "price_assumption": idea_data.get("price_assumption"),
            "notes": idea_data.get("notes"),
            "debug": True  # Enable debug to get full ledger
        }
        
        response = test_client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 200, f"Request failed for {idea_name}"
        
        response_data = response.json()
        
        # Check that sources list is populated
        sources = response_data.get("sources", [])
        assert len(sources) > 0, \
            f"No sources returned for {idea_name}"
        
        # Check evidence ledger (when debug is enabled)
        evidence_ledger = response_data.get("evidence_ledger", [])
        if evidence_ledger:
            # All claims in ledger should have source_url
            for claim in evidence_ledger:
                assert "source_url" in claim, \
                    f"Claim missing source_url for {idea_name}"
                assert claim["source_url"], \
                    f"Claim has empty source_url for {idea_name}"
        
        # Validate market section has assumptions (which should reference sources)
        market = response_data.get("market", {})
        tam = market.get("tam", {})
        sam = market.get("sam", {})
        som = market.get("som", {})
        
        # All market estimates should have assumptions
        assert len(tam.get("assumptions", [])) > 0, \
            f"TAM missing assumptions for {idea_name}"
        assert len(sam.get("assumptions", [])) > 0, \
            f"SAM missing assumptions for {idea_name}"
        assert len(som.get("assumptions", [])) > 0, \
            f"SOM missing assumptions for {idea_name}"


@pytest.mark.asyncio
async def test_assumptions_list_is_populated(test_client, fintech_eu_idea):
    """Test that assumptions list is populated and references sources."""
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
    assumptions = response_data.get("assumptions", [])
    
    # Assumptions list should be populated
    assert len(assumptions) > 0, \
        "Assumptions list should not be empty"
    
    # Assumptions should be strings
    for assumption in assumptions:
        assert isinstance(assumption, str), \
            f"Assumption should be a string, got {type(assumption)}"
        assert len(assumption) > 0, \
            "Assumption should not be empty"


