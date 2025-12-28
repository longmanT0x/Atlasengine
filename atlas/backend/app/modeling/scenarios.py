"""
Scenario Analysis Module

Implements Bear/Base/Bull scenario analysis and sensitivity analysis.

Design Decisions:
- Scenarios vary: price/ARPA, adoption rate, reachable customer count
- All calculations are deterministic (same inputs = same outputs)
- Sensitivity analysis ranks assumptions by impact on SOM
- Shows -30% and +30% impact for each assumption
"""

from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel
from app.modeling.estimation import (
    estimate_sam_from_tam,
    estimate_som_from_sam
)
from app.modeling.data_retrieval import get_pricing_facts
import statistics

# Import these after __init__.py has defined them (circular import resolved by not importing scenarios in __init__)
# Note: These imports work because __init__.py doesn't import scenarios until after defining MarketModel and MarketEstimate
from app.modeling import MarketModel, MarketEstimate


class Scenario(BaseModel):
    """Represents a scenario (Bear/Base/Bull) with market estimates."""
    name: str  # "Bear", "Base", or "Bull"
    tam: MarketEstimate
    sam: MarketEstimate
    som: MarketEstimate
    assumptions_used: Dict[str, float]  # The assumption values used in this scenario


class SensitivityImpact(BaseModel):
    """Represents sensitivity impact of an assumption on SOM."""
    assumption_name: str
    base_som: float  # Base case SOM in billions
    impact_minus_30pct: float  # SOM if assumption is -30%
    impact_plus_30pct: float  # SOM if assumption is +30%
    impact_magnitude: float  # Absolute difference between +30% and -30% impacts


def calculate_scenarios(
    base_model: MarketModel,
    price_arpa: Optional[float] = None,
    adoption_rate: Optional[float] = None,
    reachable_customers: Optional[Dict[str, float]] = None
) -> Dict[str, Scenario]:
    """
    Calculate Bear/Base/Bull scenarios varying price/ARPA, adoption rate, and customer count.
    
    Args:
        base_model: Base MarketModel from standard estimation
        price_arpa: Optional base price/ARPA (if None, derived from pricing facts)
        adoption_rate: Optional base adoption rate (if None, uses default from SOM calculation)
        reachable_customers: Optional dict with min/base/max customer counts
        
    Returns:
        Dictionary with "bear", "base", "bull" scenarios
    """
    # Get base values
    if price_arpa is None:
        pricing_facts = get_pricing_facts()
        if pricing_facts:
            prices = [f.get('value') for f in pricing_facts if f.get('value') is not None]
            if prices:
                # Convert to annual if monthly
                for i, price in enumerate(prices):
                    fact = pricing_facts[i]
                    unit = fact.get('unit', '').lower()
                    if 'month' in unit:
                        prices[i] = price * 12
                price_arpa = statistics.median(prices)
            else:
                price_arpa = 1000.0  # Default fallback
        else:
            price_arpa = 1000.0  # Default fallback
    
    # Base adoption rate (from SOM penetration assumption)
    # Calculate from base model: SOM = SAM × penetration_rate
    if adoption_rate is None:
        if base_model.sam.base > 0:
            # Derive adoption rate from base model
            adoption_rate = base_model.som.base / base_model.sam.base
        else:
            # Default from estimate_som_from_sam: 2% for 5-year horizon
            adoption_rate = 0.02
    
    # Base customer count - derive from SOM using deterministic formula
    if reachable_customers is None:
        # Estimate from SOM: SOM = customers × price × adoption_rate
        som_base = base_model.som.base * 1_000_000_000  # Convert to dollars
        if (price_arpa * adoption_rate) > 0:
            base_customers = som_base / (price_arpa * adoption_rate)
        else:
            # Fallback: estimate from SAM
            sam_base = base_model.sam.base * 1_000_000_000
            base_customers = sam_base / price_arpa if price_arpa > 0 else 10000
        
        # Use deterministic ranges based on base
        reachable_customers = {
            'min': base_customers * 0.7,  # -30% deterministic
            'base': base_customers,
            'max': base_customers * 1.3   # +30% deterministic
        }
    
    scenarios = {}
    
    # Base scenario (uses original model)
    scenarios['base'] = Scenario(
        name="Base",
        tam=base_model.tam,
        sam=base_model.sam,
        som=base_model.som,
        assumptions_used={
            'price_arpa': price_arpa,
            'adoption_rate': adoption_rate,
            'reachable_customers': reachable_customers['base']
        }
    )
    
    # Bear scenario (-30% on all three assumptions)
    bear_price = price_arpa * 0.7
    bear_adoption = adoption_rate * 0.7
    bear_customers = {
        'min': reachable_customers['min'] * 0.7,
        'base': reachable_customers['base'] * 0.7,
        'max': reachable_customers['max'] * 0.7
    }
    
    bear_som_base = (bear_customers['base'] * bear_price * bear_adoption) / 1_000_000_000
    bear_som_min = (bear_customers['min'] * bear_price * bear_adoption) / 1_000_000_000
    bear_som_max = (bear_customers['max'] * bear_price * bear_adoption) / 1_000_000_000
    
    # Bear TAM/SAM (assume same ratios as base)
    bear_tam = MarketEstimate(
        min=base_model.tam.min * 0.7,
        base=base_model.tam.base * 0.7,
        max=base_model.tam.max * 0.7,
        method=base_model.tam.method,
        formula=f"Bear scenario: {base_model.tam.formula} × 0.7",
        assumptions=base_model.tam.assumptions + [
            "Bear scenario: -30% on price, adoption, and customer count"
        ],
        sensitivity_notes=base_model.tam.sensitivity_notes,
        data_quality=base_model.tam.data_quality
    )
    
    bear_sam = MarketEstimate(
        min=base_model.sam.min * 0.7,
        base=base_model.sam.base * 0.7,
        max=base_model.sam.max * 0.7,
        method=base_model.sam.method,
        formula=f"Bear scenario: {base_model.sam.formula} × 0.7",
        assumptions=base_model.sam.assumptions + [
            "Bear scenario: -30% on price, adoption, and customer count"
        ],
        sensitivity_notes=base_model.sam.sensitivity_notes,
        data_quality=base_model.sam.data_quality
    )
    
    bear_som = MarketEstimate(
        min=bear_som_min,
        base=bear_som_base,
        max=bear_som_max,
        method="Bear scenario (bottom-up)",
        formula="SOM = Reachable Customers × Price/ARPA × Adoption Rate (Bear: all -30%)",
        assumptions=[
            f"Bear scenario: Price/ARPA = ${bear_price:,.0f} (-30%)",
            f"Bear scenario: Adoption rate = {bear_adoption*100:.1f}% (-30%)",
            f"Bear scenario: Reachable customers = {bear_customers['base']:,.0f} (-30%)"
        ],
        sensitivity_notes=["Bear scenario assumes pessimistic assumptions across all factors"],
        data_quality=base_model.som.data_quality
    )
    
    scenarios['bear'] = Scenario(
        name="Bear",
        tam=bear_tam,
        sam=bear_sam,
        som=bear_som,
        assumptions_used={
            'price_arpa': bear_price,
            'adoption_rate': bear_adoption,
            'reachable_customers': bear_customers['base']
        }
    )
    
    # Bull scenario (+30% on all three assumptions)
    bull_price = price_arpa * 1.3
    bull_adoption = adoption_rate * 1.3
    bull_customers = {
        'min': reachable_customers['min'] * 1.3,
        'base': reachable_customers['base'] * 1.3,
        'max': reachable_customers['max'] * 1.3
    }
    
    # Calculate Bull SOM using deterministic formula: SOM = Customers × Price × Adoption
    bull_som_base = (bull_customers['base'] * bull_price * bull_adoption) / 1_000_000_000
    bull_som_min = (bull_customers['min'] * bull_price * bull_adoption) / 1_000_000_000
    bull_som_max = (bull_customers['max'] * bull_price * bull_adoption) / 1_000_000_000
    
    # Ensure deterministic: same inputs always produce same outputs
    bull_som_base = round(bull_som_base, 6)
    bull_som_min = round(bull_som_min, 6)
    bull_som_max = round(bull_som_max, 6)
    
    bull_tam = MarketEstimate(
        min=base_model.tam.min * 1.3,
        base=base_model.tam.base * 1.3,
        max=base_model.tam.max * 1.3,
        method=base_model.tam.method,
        formula=f"Bull scenario: {base_model.tam.formula} × 1.3",
        assumptions=base_model.tam.assumptions + [
            "Bull scenario: +30% on price, adoption, and customer count"
        ],
        sensitivity_notes=base_model.tam.sensitivity_notes,
        data_quality=base_model.tam.data_quality
    )
    
    bull_sam = MarketEstimate(
        min=base_model.sam.min * 1.3,
        base=base_model.sam.base * 1.3,
        max=base_model.sam.max * 1.3,
        method=base_model.sam.method,
        formula=f"Bull scenario: {base_model.sam.formula} × 1.3",
        assumptions=base_model.sam.assumptions + [
            "Bull scenario: +30% on price, adoption, and customer count"
        ],
        sensitivity_notes=base_model.sam.sensitivity_notes,
        data_quality=base_model.sam.data_quality
    )
    
    bull_som = MarketEstimate(
        min=bull_som_min,
        base=bull_som_base,
        max=bull_som_max,
        method="Bull scenario (bottom-up)",
        formula="SOM = Reachable Customers × Price/ARPA × Adoption Rate (Bull: all +30%)",
        assumptions=[
            f"Bull scenario: Price/ARPA = ${bull_price:,.0f} (+30%)",
            f"Bull scenario: Adoption rate = {bull_adoption*100:.1f}% (+30%)",
            f"Bull scenario: Reachable customers = {bull_customers['base']:,.0f} (+30%)"
        ],
        sensitivity_notes=["Bull scenario assumes optimistic assumptions across all factors"],
        data_quality=base_model.som.data_quality
    )
    
    scenarios['bull'] = Scenario(
        name="Bull",
        tam=bull_tam,
        sam=bull_sam,
        som=bull_som,
        assumptions_used={
            'price_arpa': bull_price,
            'adoption_rate': bull_adoption,
            'reachable_customers': bull_customers['base']
        }
    )
    
    return scenarios


def calculate_sensitivity_analysis(
    base_model: MarketModel,
    price_arpa: Optional[float] = None,
    adoption_rate: Optional[float] = None,
    reachable_customers: Optional[Dict[str, float]] = None
) -> List[SensitivityImpact]:
    """
    Calculate sensitivity analysis ranking top 5 assumptions by impact on SOM.
    
    For each assumption, shows impact of -30% and +30% changes.
    
    Args:
        base_model: Base MarketModel
        price_arpa: Optional base price/ARPA
        adoption_rate: Optional base adoption rate
        reachable_customers: Optional base customer counts
        
    Returns:
        List of SensitivityImpact objects ranked by impact magnitude
    """
    # Get base values (same logic as scenarios)
    if price_arpa is None:
        pricing_facts = get_pricing_facts()
        if pricing_facts:
            prices = [f.get('value') for f in pricing_facts if f.get('value') is not None]
            if prices:
                for i, price in enumerate(prices):
                    fact = pricing_facts[i]
                    unit = fact.get('unit', '').lower()
                    if 'month' in unit:
                        prices[i] = price * 12
                price_arpa = statistics.median(prices)
            else:
                price_arpa = 1000.0
        else:
            price_arpa = 1000.0
    
    if adoption_rate is None:
        adoption_rate = 0.02
    
    if reachable_customers is None:
        som_base = base_model.som.base * 1_000_000_000
        base_customers = som_base / (price_arpa * adoption_rate) if (price_arpa * adoption_rate) > 0 else 10000
        reachable_customers = {
            'min': base_customers * 0.7,
            'base': base_customers,
            'max': base_customers * 1.3
        }
    
    base_som = base_model.som.base
    
    # Calculate sensitivity for each assumption
    sensitivities = []
    
    # 1. Price/ARPA sensitivity (deterministic calculation)
    som_minus_price = round(((reachable_customers['base'] * price_arpa * 0.7 * adoption_rate) / 1_000_000_000), 6)
    som_plus_price = round(((reachable_customers['base'] * price_arpa * 1.3 * adoption_rate) / 1_000_000_000), 6)
    sensitivities.append(SensitivityImpact(
        assumption_name="Price/ARPA",
        base_som=round(base_som, 6),
        impact_minus_30pct=som_minus_price,
        impact_plus_30pct=som_plus_price,
        impact_magnitude=round(abs(som_plus_price - som_minus_price), 6)
    ))
    
    # 2. Adoption rate sensitivity (deterministic calculation)
    som_minus_adoption = round(((reachable_customers['base'] * price_arpa * adoption_rate * 0.7) / 1_000_000_000), 6)
    som_plus_adoption = round(((reachable_customers['base'] * price_arpa * adoption_rate * 1.3) / 1_000_000_000), 6)
    sensitivities.append(SensitivityImpact(
        assumption_name="Adoption Rate",
        base_som=round(base_som, 6),
        impact_minus_30pct=som_minus_adoption,
        impact_plus_30pct=som_plus_adoption,
        impact_magnitude=round(abs(som_plus_adoption - som_minus_adoption), 6)
    ))
    
    # 3. Reachable customer count sensitivity (deterministic calculation)
    som_minus_customers = round(((reachable_customers['base'] * 0.7 * price_arpa * adoption_rate) / 1_000_000_000), 6)
    som_plus_customers = round(((reachable_customers['base'] * 1.3 * price_arpa * adoption_rate) / 1_000_000_000), 6)
    sensitivities.append(SensitivityImpact(
        assumption_name="Reachable Customer Count",
        base_som=round(base_som, 6),
        impact_minus_30pct=som_minus_customers,
        impact_plus_30pct=som_plus_customers,
        impact_magnitude=round(abs(som_plus_customers - som_minus_customers), 6)
    ))
    
    # 4. TAM sensitivity (affects SAM and SOM through serviceable market %)
    # Serviceable market % from SAM calculation (deterministic)
    serviceable_pct_base = base_model.sam.base / base_model.tam.base if base_model.tam.base > 0 else 0.1
    tam_minus = round(base_model.tam.base * 0.7, 6)
    tam_plus = round(base_model.tam.base * 1.3, 6)
    sam_minus = round(tam_minus * serviceable_pct_base, 6)
    sam_plus = round(tam_plus * serviceable_pct_base, 6)
    # SOM from SAM (using penetration rate - deterministic)
    penetration_pct = base_model.som.base / base_model.sam.base if base_model.sam.base > 0 else 0.02
    som_minus_tam = round(sam_minus * penetration_pct, 6)
    som_plus_tam = round(sam_plus * penetration_pct, 6)
    sensitivities.append(SensitivityImpact(
        assumption_name="TAM (Total Addressable Market)",
        base_som=round(base_som, 6),
        impact_minus_30pct=som_minus_tam,
        impact_plus_30pct=som_plus_tam,
        impact_magnitude=round(abs(som_plus_tam - som_minus_tam), 6)
    ))
    
    # 5. Serviceable Market % sensitivity (deterministic)
    serviceable_pct_minus = round(serviceable_pct_base * 0.7, 6)
    serviceable_pct_plus = round(serviceable_pct_base * 1.3, 6)
    sam_minus_serviceable = round(base_model.tam.base * serviceable_pct_minus, 6)
    sam_plus_serviceable = round(base_model.tam.base * serviceable_pct_plus, 6)
    som_minus_serviceable = round(sam_minus_serviceable * penetration_pct, 6)
    som_plus_serviceable = round(sam_plus_serviceable * penetration_pct, 6)
    sensitivities.append(SensitivityImpact(
        assumption_name="Serviceable Market % (SAM/TAM)",
        base_som=round(base_som, 6),
        impact_minus_30pct=som_minus_serviceable,
        impact_plus_30pct=som_plus_serviceable,
        impact_magnitude=round(abs(som_plus_serviceable - som_minus_serviceable), 6)
    ))
    
    # Sort by impact magnitude (descending) and return top 5
    sensitivities.sort(key=lambda x: x.impact_magnitude, reverse=True)
    return sensitivities[:5]

