"""
Modeling Module

Creates probabilistic models of market dynamics under uncertainty.

Design Decisions:
- All models output ranges, never single point estimates
- Models are based on extracted facts with source traceability
- Supports both top-down and bottom-up estimation methods
- Exposes all modeling assumptions explicitly
- Widens ranges when data quality is low
- Performs sensitivity analysis to identify key assumptions
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.modeling.data_retrieval import (
    get_extracted_facts,
    get_market_size_facts,
    get_pricing_facts,
    assess_data_quality
)
from app.modeling.estimation import (
    estimate_tam_top_down,
    estimate_sam_from_tam,
    estimate_som_from_sam,
    estimate_bottom_up
)


class MarketEstimate(BaseModel):
    """Represents a market size estimate with uncertainty ranges."""
    min: float  # Minimum estimate in billions USD
    base: float  # Base case estimate in billions USD
    max: float  # Maximum estimate in billions USD
    method: str  # 'top-down' or 'bottom-up'
    formula: str  # Formula used for calculation
    assumptions: List[str]  # All assumptions made
    sensitivity_notes: List[str]  # Notes on which assumptions impact results most
    data_quality: str  # 'high', 'medium', or 'low'


class MarketModel(BaseModel):
    """Represents a complete market model with TAM/SAM/SOM."""
    tam: MarketEstimate
    sam: MarketEstimate
    som: MarketEstimate
    evidence_sources: List[str]  # Source URLs used
    overall_confidence: str  # 'high', 'medium', or 'low'


def estimate_tam_sam_som(
    customer_type: str,
    geography: str,
    estimated_customers: Optional[Dict[str, float]] = None,
    market_penetration_years: int = 5
) -> MarketModel:
    """
    Estimate TAM, SAM, and SOM using available data.
    
    Uses top-down method by default (reported market sizes).
    Falls back to bottom-up if pricing data is available but no market size data.
    
    Args:
        customer_type: Type of target customers
        geography: Target geography
        estimated_customers: Optional dict with min/base/max customer counts for bottom-up
        market_penetration_years: Years to achieve market penetration (default 5)
        
    Returns:
        MarketModel with TAM/SAM/SOM estimates including ranges, methods, formulas, assumptions
        
    Raises:
        ValueError: If insufficient data for any estimation method
    """
    # Get extracted facts
    facts = get_extracted_facts()
    market_size_facts = facts.get('market_size', [])
    pricing_facts = facts.get('pricing', [])
    
    # Assess data quality
    market_size_quality = assess_data_quality(market_size_facts)
    pricing_quality = assess_data_quality(pricing_facts)
    
    # Collect source URLs
    source_urls = set()
    for fact in market_size_facts + pricing_facts:
        url = fact.get('source_url')
        if url:
            source_urls.add(url)
    
    # Estimate TAM
    if market_size_facts:
        # Use top-down method
        tam_estimate = estimate_tam_top_down(
            market_size_facts,
            market_size_quality['quality_score']
        )
    elif pricing_facts and estimated_customers:
        # Fall back to bottom-up if no market size data but have pricing
        tam_estimate = estimate_bottom_up(
            pricing_facts,
            estimated_customers,
            pricing_quality['quality_score']
        )
        tam_estimate['method'] = 'bottom-up (TAM approximation)'
        tam_estimate['assumptions'].append(
            'TAM estimated using bottom-up method due to lack of reported market size data'
        )
    else:
        raise ValueError(
            "Insufficient data for TAM estimation. Need either market size facts "
            "or pricing facts with customer estimates."
        )
    
    # Estimate SAM from TAM
    sam_estimate = estimate_sam_from_tam(tam_estimate, customer_type, geography)
    
    # Estimate SOM from SAM
    som_estimate = estimate_som_from_sam(sam_estimate, market_penetration_years)
    
    # Determine overall confidence
    data_qualities = [
        tam_estimate.get('data_quality', 'low'),
        sam_estimate.get('data_quality', 'low'),
        som_estimate.get('data_quality', 'low')
    ]
    
    if all(q == 'high' for q in data_qualities):
        overall_confidence = 'high'
    elif any(q == 'high' for q in data_qualities):
        overall_confidence = 'medium'
    else:
        overall_confidence = 'low'
    
    return MarketModel(
        tam=MarketEstimate(**tam_estimate),
        sam=MarketEstimate(**sam_estimate),
        som=MarketEstimate(**som_estimate),
        evidence_sources=list(source_urls),
        overall_confidence=overall_confidence
    )


def create_market_model(
    extracted_facts: List[Any],
    market_parameters: Dict[str, Any]
) -> MarketModel:
    """
    Create a probabilistic market model from extracted facts.
    
    This is a wrapper function that maintains backward compatibility.
    
    Args:
        extracted_facts: List of extracted facts (not used directly, retrieved from DB)
        market_parameters: Dictionary with customer_type, geography, etc.
        
    Returns:
        MarketModel with uncertainty ranges and exposed assumptions
        
    Raises:
        ValueError: If insufficient data for modeling
    """
    customer_type = market_parameters.get('customer_type', 'Unknown')
    geography = market_parameters.get('geography', 'Unknown')
    estimated_customers = market_parameters.get('estimated_customers')
    market_penetration_years = market_parameters.get('market_penetration_years', 5)
    
    return estimate_tam_sam_som(
        customer_type=customer_type,
        geography=geography,
        estimated_customers=estimated_customers,
        market_penetration_years=market_penetration_years
    )
