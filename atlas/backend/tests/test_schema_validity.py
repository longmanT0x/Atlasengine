"""
Test response schema validity.

Ensures all responses conform to the expected schema structure.
"""

import pytest
from app.api.schemas import AnalyzeResponse
from tests.fixtures.sample_ideas import get_all_test_ideas


@pytest.mark.asyncio
async def test_response_schema_validity(test_client, sample_ideas):
    """
    Test that all responses conform to the AnalyzeResponse schema.
    
    This test validates:
    - All required fields are present
    - Field types are correct
    - Field constraints are met
    """
    for idea_name, idea_data in sample_ideas.items():
        # Prepare request
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
        
        # Make request
        response = test_client.post("/api/v1/analyze", json=request_data)
        
        # Assert response is successful
        assert response.status_code == 200, f"Request failed for {idea_name}: {response.text}"
        
        # Parse response
        response_data = response.json()
        
        # Validate against schema
        try:
            analyze_response = AnalyzeResponse(**response_data)
            
            # Additional validations
            assert analyze_response.verdict in ["GO", "NO-GO", "CONDITIONAL"], \
                f"Invalid verdict for {idea_name}: {analyze_response.verdict}"
            
            assert 0 <= analyze_response.confidence_score <= 100, \
                f"Invalid confidence score for {idea_name}: {analyze_response.confidence_score}"
            
            assert len(analyze_response.executive_summary) >= 8, \
                f"Executive summary too short for {idea_name}"
            
            assert len(analyze_response.executive_summary) <= 12, \
                f"Executive summary too long for {idea_name}"
            
            assert len(analyze_response.key_unknowns) == 5, \
                f"Expected 5 key unknowns for {idea_name}, got {len(analyze_response.key_unknowns)}"
            
            assert len(analyze_response.next_7_days_tests) == 6, \
                f"Expected 6 tests for {idea_name}, got {len(analyze_response.next_7_days_tests)}"
            
            # Validate market section
            assert analyze_response.market.tam.min >= 0, \
                f"TAM min must be non-negative for {idea_name}"
            assert analyze_response.market.tam.base >= analyze_response.market.tam.min, \
                f"TAM base must be >= min for {idea_name}"
            assert analyze_response.market.tam.max >= analyze_response.market.tam.base, \
                f"TAM max must be >= base for {idea_name}"
            
            # Validate scenarios
            assert "bear" in analyze_response.scenarios, \
                f"Missing bear scenario for {idea_name}"
            assert "base" in analyze_response.scenarios, \
                f"Missing base scenario for {idea_name}"
            assert "bull" in analyze_response.scenarios, \
                f"Missing bull scenario for {idea_name}"
            
            # Validate sensitivity analysis
            assert len(analyze_response.sensitivity_analysis) == 5, \
                f"Expected 5 sensitivity impacts for {idea_name}, got {len(analyze_response.sensitivity_analysis)}"
            
        except Exception as e:
            pytest.fail(f"Schema validation failed for {idea_name}: {str(e)}")


@pytest.mark.asyncio
async def test_debug_mode_includes_ledger(test_client, fintech_eu_idea):
    """Test that debug mode includes the evidence ledger."""
    request_data = {
        "idea": fintech_eu_idea["idea"],
        "industry": fintech_eu_idea["industry"],
        "geography": fintech_eu_idea["geography"],
        "customer_type": fintech_eu_idea["customer_type"],
        "business_model": fintech_eu_idea["business_model"],
        "price_assumption": fintech_eu_idea.get("price_assumption"),
        "notes": fintech_eu_idea.get("notes"),
        "debug": True
    }
    
    response = test_client.post("/api/v1/analyze", json=request_data)
    assert response.status_code == 200
    
    response_data = response.json()
    analyze_response = AnalyzeResponse(**response_data)
    
    # When debug is enabled, evidence_ledger should be present
    assert analyze_response.evidence_ledger is not None, \
        "Evidence ledger should be included when debug=true"
    
    # Ledger should be a list
    assert isinstance(analyze_response.evidence_ledger, list), \
        "Evidence ledger should be a list"


