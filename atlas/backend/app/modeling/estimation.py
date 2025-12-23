"""
Estimation Module

Implements TAM/SAM/SOM estimation using top-down and bottom-up methods.

Design Decisions:
- Always outputs ranges (min/base/max), never single numbers
- Widens ranges when data quality is low
- Explicitly documents formulas and assumptions
- Performs sensitivity analysis to identify key assumptions
"""

from typing import Dict, Any, List, Tuple, Optional
import statistics


def normalize_to_billions(value: float, unit: str) -> float:
    """
    Normalize a value to billions USD.
    
    Args:
        value: Numeric value
        unit: Unit string (e.g., 'billion', 'million', 'thousand')
        
    Returns:
        Value in billions
    """
    unit_lower = unit.lower() if unit else ''
    
    if 'trillion' in unit_lower:
        return value * 1000
    elif 'billion' in unit_lower or 'b' in unit_lower:
        return value
    elif 'million' in unit_lower or 'm' in unit_lower:
        return value / 1000
    elif 'thousand' in unit_lower or 'k' in unit_lower:
        return value / 1000000
    else:
        # Assume billions if unit unclear
        return value


def calculate_range_from_values(
    values: List[float],
    data_quality: str,
    has_low_credibility: bool = False
) -> Tuple[float, float, float]:
    """
    Calculate min/base/max range from a list of values.
    
    If low credibility sources exist, ranges are widened significantly.
    
    Args:
        values: List of numeric values
        data_quality: 'high', 'medium', or 'low'
        has_low_credibility: Whether low credibility sources exist
        
    Returns:
        Tuple of (min, base, max) in billions
    """
    if not values:
        return (0.0, 0.0, 0.0)
    
    # Base case is median
    base = statistics.median(values)
    min_val = min(values)
    max_val = max(values)
    
    # Adjust range based on data quality and credibility
    if has_low_credibility:
        # Widen range significantly for low credibility sources
        range_factor = 1.0  # 100% wider (double the range)
        range_size = (max_val - min_val) * (1 + range_factor)
        center = (min_val + max_val) / 2
        min_val = max(0, center - range_size / 2)
        max_val = center + range_size / 2
    elif data_quality == 'low':
        # Widen range significantly for low quality data
        range_factor = 0.5  # 50% wider
        range_size = (max_val - min_val) * (1 + range_factor)
        center = (min_val + max_val) / 2
        min_val = max(0, center - range_size / 2)
        max_val = center + range_size / 2
    elif data_quality == 'medium':
        # Moderate widening
        range_factor = 0.25  # 25% wider
        range_size = (max_val - min_val) * (1 + range_factor)
        center = (min_val + max_val) / 2
        min_val = max(0, center - range_size / 2)
        max_val = center + range_size / 2
    
    return (min_val, base, max_val)


def estimate_tam_top_down(
    market_size_facts: List[Dict[str, Any]],
    data_quality: str
) -> Dict[str, Any]:
    """
    Estimate TAM using top-down method (reported market sizes).
    
    Formula: TAM = Reported market size from industry sources
    
    Args:
        market_size_facts: List of extracted market size facts
        data_quality: Quality assessment of the data
        
    Returns:
        Dictionary with TAM estimate including ranges, method, formula, assumptions
    """
    if not market_size_facts:
        return {
            'min': 0.0,
            'base': 0.0,
            'max': 0.0,
            'method': 'top-down',
            'formula': 'TAM = Reported market size (no data available)',
            'assumptions': [
                'No market size data found in sources',
                'Estimate cannot be calculated without reported market sizes'
            ],
            'sensitivity_notes': [
                'No data available for sensitivity analysis'
            ],
            'data_quality': 'low'
        }
    
    # Extract and normalize values
    values = []
    for fact in market_size_facts:
        value = fact.get('value')
        unit = fact.get('unit', '')
        if value is not None:
            normalized = normalize_to_billions(float(value), unit)
            values.append(normalized)
    
    if not values:
        return {
            'min': 0.0,
            'base': 0.0,
            'max': 0.0,
            'method': 'top-down',
            'formula': 'TAM = Reported market size (no numeric values found)',
            'assumptions': [
                'Market size facts found but no numeric values extracted',
                'Values may be in non-standard format'
            ],
            'sensitivity_notes': [
                'No numeric data available for sensitivity analysis'
            ],
            'data_quality': 'low'
        }
    
    # Check for low credibility sources
    from app.evidence.ledger import has_low_credibility_claims
    has_low_cred = has_low_credibility_claims('market_size')
    
    min_val, base, max_val = calculate_range_from_values(values, data_quality, has_low_cred)
    
    # Add note about low credibility if present
    if has_low_cred:
        assumptions.append('Low credibility sources detected - ranges widened to account for uncertainty')
    
    # Build assumptions list
    assumptions = [
        f'Based on {len(values)} reported market size figure(s) from industry sources',
        'Assumes reported figures are accurate and current',
        'Assumes figures represent total addressable market (TAM)',
        f'Data quality assessed as: {data_quality}'
    ]
    
    # Sensitivity analysis
    if len(values) > 1:
        value_range = max(values) - min(values)
        avg_value = statistics.mean(values)
        variation_pct = (value_range / avg_value * 100) if avg_value > 0 else 0
        
        sensitivity_notes = [
            f'Market size values vary by {variation_pct:.1f}% across sources',
            'Most sensitive to: Source credibility and recency of data',
            f'Range spans from ${min(values):.2f}B to ${max(values):.2f}B'
        ]
        
        if variation_pct > 50:
            sensitivity_notes.append(
                'High variation suggests market definition may differ across sources'
            )
    else:
        sensitivity_notes = [
            'Single data point - high uncertainty',
            'Most sensitive to: Accuracy of the single source',
            'Recommendation: Seek additional market size sources'
        ]
    
    return {
        'min': min_val,
        'base': base,
        'max': max_val,
        'method': 'top-down',
        'formula': 'TAM = Reported market size from industry sources',
        'assumptions': assumptions,
        'sensitivity_notes': sensitivity_notes,
        'data_quality': data_quality
    }


def estimate_sam_from_tam(
    tam_estimate: Dict[str, Any],
    customer_type: str,
    geography: str
) -> Dict[str, Any]:
    """
    Estimate SAM from TAM using segmentation assumptions.
    
    Formula: SAM = TAM × Serviceable Market Percentage
    
    Args:
        tam_estimate: TAM estimate dictionary
        customer_type: Type of target customers
        geography: Target geography
        
    Returns:
        Dictionary with SAM estimate
    """
    # Default serviceable market percentages (conservative)
    # These are assumptions that should be validated
    serviceable_pct_min = 0.05  # 5% of TAM
    serviceable_pct_base = 0.10  # 10% of TAM
    serviceable_pct_max = 0.20  # 20% of TAM
    
    # Adjust based on customer type and geography
    if 'enterprise' in customer_type.lower() or 'b2b' in customer_type.lower():
        serviceable_pct_min = 0.02
        serviceable_pct_base = 0.05
        serviceable_pct_max = 0.10
    elif 'consumer' in customer_type.lower() or 'b2c' in customer_type.lower():
        serviceable_pct_min = 0.10
        serviceable_pct_base = 0.20
        serviceable_pct_max = 0.40
    
    tam_min = tam_estimate.get('min', 0)
    tam_base = tam_estimate.get('base', 0)
    tam_max = tam_estimate.get('max', 0)
    
    sam_min = tam_min * serviceable_pct_min
    sam_base = tam_base * serviceable_pct_base
    sam_max = tam_max * serviceable_pct_max
    
    assumptions = [
        f'SAM calculated as {serviceable_pct_base*100:.0f}% of TAM (base case)',
        f'Serviceable market range: {serviceable_pct_min*100:.0f}% - {serviceable_pct_max*100:.0f}% of TAM',
        f'Based on customer type: {customer_type}',
        f'Based on geography: {geography}',
        'Assumes product/service is relevant to this customer segment',
        'Assumes geographic constraints are applicable'
    ]
    
    sensitivity_notes = [
        f'Most sensitive to: Serviceable market percentage assumption ({serviceable_pct_base*100:.0f}% base)',
        f'1% change in serviceable % = ${tam_base * 0.01:.2f}B change in SAM',
        'Recommendation: Validate serviceable market percentage with industry benchmarks'
    ]
    
    return {
        'min': sam_min,
        'base': sam_base,
        'max': sam_max,
        'method': 'top-down (derived from TAM)',
        'formula': f'SAM = TAM × Serviceable Market % (range: {serviceable_pct_min*100:.0f}% - {serviceable_pct_max*100:.0f}%)',
        'assumptions': assumptions,
        'sensitivity_notes': sensitivity_notes,
        'data_quality': tam_estimate.get('data_quality', 'medium')
    }


def estimate_som_from_sam(
    sam_estimate: Dict[str, Any],
    market_penetration_years: int = 5
) -> Dict[str, Any]:
    """
    Estimate SOM from SAM using market penetration assumptions.
    
    Formula: SOM = SAM × Market Penetration Percentage
    
    Args:
        sam_estimate: SAM estimate dictionary
        market_penetration_years: Years to achieve penetration (default 5)
        
    Returns:
        Dictionary with SOM estimate
    """
    # Conservative penetration assumptions
    # Year 1-2: 0.5-1%, Year 3-5: 1-3%, Year 5+: 3-5%
    if market_penetration_years <= 2:
        penetration_min = 0.005  # 0.5%
        penetration_base = 0.01  # 1%
        penetration_max = 0.02  # 2%
    elif market_penetration_years <= 5:
        penetration_min = 0.01  # 1%
        penetration_base = 0.02  # 2%
        penetration_max = 0.05  # 5%
    else:
        penetration_min = 0.02  # 2%
        penetration_base = 0.03  # 3%
        penetration_max = 0.05  # 5%
    
    sam_min = sam_estimate.get('min', 0)
    sam_base = sam_estimate.get('base', 0)
    sam_max = sam_estimate.get('max', 0)
    
    som_min = sam_min * penetration_min
    som_base = sam_base * penetration_base
    som_max = sam_max * penetration_max
    
    assumptions = [
        f'SOM calculated as {penetration_base*100:.1f}% of SAM (base case)',
        f'Market penetration range: {penetration_min*100:.1f}% - {penetration_max*100:.1f}% of SAM',
        f'Time horizon: {market_penetration_years} years',
        'Assumes realistic market penetration based on typical startup growth',
        'Assumes effective go-to-market strategy execution'
    ]
    
    sensitivity_notes = [
        f'Most sensitive to: Market penetration percentage ({penetration_base*100:.1f}% base)',
        f'1% change in penetration = ${sam_base * 0.01:.2f}B change in SOM',
        'Recommendation: Validate penetration assumptions with comparable company benchmarks',
        f'Time horizon of {market_penetration_years} years significantly impacts estimate'
    ]
    
    return {
        'min': som_min,
        'base': som_base,
        'max': som_max,
        'method': 'top-down (derived from SAM)',
        'formula': f'SOM = SAM × Market Penetration % (range: {penetration_min*100:.1f}% - {penetration_max*100:.1f}%)',
        'assumptions': assumptions,
        'sensitivity_notes': sensitivity_notes,
        'data_quality': sam_estimate.get('data_quality', 'medium')
    }


def estimate_bottom_up(
    pricing_facts: List[Dict[str, Any]],
    estimated_customers: Dict[str, float],
    data_quality: str
) -> Dict[str, Any]:
    """
    Estimate market size using bottom-up method (customers × price).
    
    Formula: Market Size = Number of Customers × Average Price × Penetration Rate
    
    Args:
        pricing_facts: List of extracted pricing facts
        estimated_customers: Dictionary with min/base/max customer counts
        data_quality: Quality assessment of the data
        
    Returns:
        Dictionary with market size estimate
    """
    # Extract pricing values
    prices = []
    for fact in pricing_facts:
        value = fact.get('value')
        if value is not None:
            # Assume prices are in USD, convert to annual if monthly
            unit = fact.get('unit', '').lower()
            if 'month' in unit:
                value = value * 12  # Convert to annual
            prices.append(float(value))
    
    if not prices:
        return {
            'min': 0.0,
            'base': 0.0,
            'max': 0.0,
            'method': 'bottom-up',
            'formula': 'Market Size = Customers × Price (no pricing data available)',
            'assumptions': [
                'No pricing data found in sources',
                'Cannot calculate bottom-up estimate without pricing information'
            ],
            'sensitivity_notes': [
                'No pricing data available for sensitivity analysis'
            ],
            'data_quality': 'low'
        }
    
    # Calculate average price
    avg_price_min = min(prices)
    avg_price_base = statistics.median(prices)
    avg_price_max = max(prices)
    
    # Get customer estimates
    customers_min = estimated_customers.get('min', 0)
    customers_base = estimated_customers.get('base', 0)
    customers_max = estimated_customers.get('max', 0)
    
    # Calculate market size (in billions)
    market_size_min = (customers_min * avg_price_min) / 1_000_000_000
    market_size_base = (customers_base * avg_price_base) / 1_000_000_000
    market_size_max = (customers_max * avg_price_max) / 1_000_000_000
    
    assumptions = [
        f'Based on {len(prices)} pricing data point(s)',
        f'Average price range: ${avg_price_min:,.0f} - ${avg_price_max:,.0f} (base: ${avg_price_base:,.0f})',
        f'Customer count range: {customers_min:,.0f} - {customers_max:,.0f} (base: {customers_base:,.0f})',
        'Assumes all customers pay average price',
        'Assumes 100% market penetration (no discounting)',
        f'Data quality assessed as: {data_quality}'
    ]
    
    # Sensitivity analysis
    price_sensitivity = customers_base * (avg_price_max - avg_price_min) / 1_000_000_000
    customer_sensitivity = avg_price_base * (customers_max - customers_min) / 1_000_000_000
    
    if price_sensitivity > customer_sensitivity:
        most_sensitive = 'Price assumption'
        sensitivity_value = f'${price_sensitivity:.2f}B'
    else:
        most_sensitive = 'Customer count assumption'
        sensitivity_value = f'${customer_sensitivity:.2f}B'
    
    sensitivity_notes = [
        f'Most sensitive to: {most_sensitive}',
        f'Range impact: {sensitivity_value}',
        'Recommendation: Validate both customer count and pricing assumptions independently'
    ]
    
    return {
        'min': market_size_min,
        'base': market_size_base,
        'max': market_size_max,
        'method': 'bottom-up',
        'formula': 'Market Size = Number of Customers × Average Price',
        'assumptions': assumptions,
        'sensitivity_notes': sensitivity_notes,
        'data_quality': data_quality
    }

