"""
Sample startup ideas for testing.

Each idea includes:
- Request data
- Expected characteristics (not exact numbers, but ranges/patterns)
- Expected minimum thresholds
"""

from typing import Dict, Any

# FinTech idea (EU)
FINTECH_EU_IDEA = {
    "idea": "AI-powered personal finance management app that helps EU consumers optimize savings and investments",
    "industry": "FinTech",
    "geography": "European Union",
    "customer_type": "B2C consumers",
    "business_model": "Freemium subscription with premium features",
    "price_assumption": 9.99,  # Monthly subscription
    "notes": "Focus on GDPR compliance and multi-currency support",
    "expected_characteristics": {
        "min_sources": 5,
        "min_competitors": 3,  # FinTech has many competitors
        "expected_market_size_range": (1.0, 50.0),  # Billions USD
        "expected_risks": ["regulatory", "competition"],
        "expected_confidence_range": (40, 80),  # Should be moderate to high
        "should_have_regulatory_risks": True,
        "should_have_pricing_data": True
    }
}

# Travel marketplace (Belgium)
TRAVEL_BELGIUM_IDEA = {
    "idea": "Local travel marketplace connecting Belgian travelers with unique local experiences and accommodations",
    "industry": "Travel & Tourism",
    "geography": "Belgium",
    "customer_type": "B2C consumers",
    "business_model": "Commission-based marketplace",
    "price_assumption": 15.0,  # Average commission per booking
    "notes": "Focus on sustainable and local tourism",
    "expected_characteristics": {
        "min_sources": 5,
        "min_competitors": 5,  # Travel has many established players
        "expected_market_size_range": (0.1, 10.0),  # Billions USD (smaller geography)
        "expected_risks": ["competition", "market"],
        "expected_confidence_range": (30, 70),
        "should_have_regulatory_risks": False,  # Less regulatory in travel
        "should_have_pricing_data": True
    }
}

# B2B SaaS niche (Benelux)
B2B_SAAS_BENELUX_IDEA = {
    "idea": "Specialized B2B SaaS platform for supply chain management in the Benelux manufacturing sector",
    "industry": "B2B SaaS",
    "geography": "Benelux (Belgium, Netherlands, Luxembourg)",
    "customer_type": "B2B Enterprise",
    "business_model": "Subscription-based SaaS",
    "price_assumption": 500.0,  # Monthly per enterprise
    "notes": "Niche focus on manufacturing supply chains",
    "expected_characteristics": {
        "min_sources": 5,
        "min_competitors": 2,  # Niche market, fewer competitors
        "expected_market_size_range": (0.01, 5.0),  # Billions USD (niche market)
        "expected_risks": ["competition", "distribution"],
        "expected_confidence_range": (25, 65),  # Niche markets have less data
        "should_have_regulatory_risks": False,
        "should_have_pricing_data": True
    }
}

# Helper function to get all test ideas
def get_all_test_ideas() -> Dict[str, Dict[str, Any]]:
    """Get all test ideas as a dictionary."""
    return {
        "fintech_eu": FINTECH_EU_IDEA,
        "travel_belgium": TRAVEL_BELGIUM_IDEA,
        "b2b_saas_benelux": B2B_SAAS_BENELUX_IDEA
    }


