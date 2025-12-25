from __future__ import annotations
"""
Risk Analysis Module

Analyzes risks from extracted data grouped by category.
"""

from typing import List, Dict, Any
import statistics


def analyze_market_risks(
    market_size_facts: List[Dict[str, Any]],
    growth_rate_facts: List[Dict[str, Any]]
) -> List[str]:
    """
    Analyze market-specific risks from extracted data.
    
    Args:
        market_size_facts: List of market size facts
        growth_rate_facts: List of growth rate facts
        
    Returns:
        List of specific market risk statements
    """
    risks = []
    
    # Analyze market size data quality
    if not market_size_facts:
        risks.append(
            "No market size data found in sources - market size estimates are highly uncertain"
        )
    elif len(market_size_facts) == 1:
        risks.append(
            f"Only one market size data point found - high uncertainty in market size estimate "
            f"(source: {market_size_facts[0].get('source_url', 'unknown')})"
        )
    else:
        # Check for high variation in market size estimates
        values = [f.get('value') for f in market_size_facts if f.get('value') is not None]
        if len(values) > 1:
            value_range = max(values) - min(values)
            avg_value = statistics.mean(values)
            variation_pct = (value_range / avg_value * 100) if avg_value > 0 else 0
            
            if variation_pct > 50:
                risks.append(
                    f"Market size estimates vary by {variation_pct:.1f}% across sources - "
                    f"suggests inconsistent market definitions or data quality issues"
                )
    
    # Analyze growth rate data
    if not growth_rate_facts:
        risks.append(
            "No growth rate data found - cannot assess market growth trajectory"
        )
    else:
        growth_values = [f.get('value') for f in growth_rate_facts if f.get('value') is not None]
        if growth_values:
            avg_growth = statistics.mean(growth_values)
            min_growth = min(growth_values)
            
            if avg_growth < 5:
                risks.append(
                    f"Market growth rate is low ({avg_growth:.1f}% average) - "
                    f"indicates slow-growing or mature market"
                )
            elif min_growth < 0:
                risks.append(
                    f"Some sources indicate negative growth ({min_growth:.1f}%) - "
                    f"market may be declining"
                )
    
    # Check for inferred data
    inferred_count = sum(1 for f in market_size_facts if f.get('is_inferred', False))
    if inferred_count > 0:
        risks.append(
            f"{inferred_count} market size fact(s) marked as inferred - "
            f"data quality may be insufficient for reliable estimates"
        )
    
    return risks


def analyze_competition_risks(
    competitor_facts: List[Dict[str, Any]],
    competitor_analysis: List[Dict[str, Any]]
) -> List[str]:
    """
    Analyze competition-specific risks from extracted data.
    
    Args:
        competitor_facts: List of competitor facts
        competitor_analysis: List of analyzed competitor dictionaries
        
    Returns:
        List of specific competition risk statements
    """
    risks = []
    
    if not competitor_facts:
        risks.append(
            "No competitor data found - competitive landscape is unknown"
        )
        return risks
    
    # Analyze number of competitors
    unique_competitors = len(competitor_analysis)
    
    if unique_competitors == 0:
        risks.append(
            "No competitors identified - may indicate new market or incomplete research"
        )
    elif unique_competitors >= 10:
        risks.append(
            f"High number of competitors identified ({unique_competitors}) - "
            f"indicates crowded, competitive market"
        )
    elif unique_competitors >= 5:
        risks.append(
            f"Moderate number of competitors ({unique_competitors}) - "
            f"market has established players"
        )
    
    # Analyze competitor positioning overlap
    positioning_counts = {}
    for comp in competitor_analysis:
        positioning = comp.get('positioning', 'General market')
        positioning_counts[positioning] = positioning_counts.get(positioning, 0) + 1
    
    # Check for positioning concentration
    max_positioning_count = max(positioning_counts.values()) if positioning_counts else 0
    if max_positioning_count >= 3 and unique_competitors >= 5:
        most_common = max(positioning_counts.items(), key=lambda x: x[1])
        risks.append(
            f"Multiple competitors ({most_common[1]}) targeting same positioning "
            f"({most_common[0]}) - high competition in this segment"
        )
    
    # Check for established players
    mention_counts = [comp.get('mention_count', 0) for comp in competitor_analysis]
    if mention_counts:
        max_mentions = max(mention_counts)
        if max_mentions >= 3:
            highly_mentioned = [c for c in competitor_analysis if c.get('mention_count', 0) >= 3]
            risks.append(
                f"Several competitors mentioned frequently ({len(highly_mentioned)}) - "
                f"indicates well-established market leaders"
            )
    
    return risks


def analyze_regulatory_risks(
    regulatory_facts: List[Dict[str, Any]]
) -> List[str]:
    """
    Analyze regulatory-specific risks from extracted data.
    
    Args:
        regulatory_facts: List of regulatory facts
        
    Returns:
        List of specific regulatory risk statements
    """
    risks = []
    
    if not regulatory_facts:
        risks.append(
            "No regulatory mentions found - regulatory requirements may be unknown or unassessed"
        )
        return risks
    
    # Analyze regulatory mentions
    regulatory_mentions = [f.get('value', '') for f in regulatory_facts]
    contexts = [f.get('context_sentence', '').lower() for f in regulatory_facts]
    
    # Check for specific regulatory agencies
    agencies = {
        'FDA': 'FDA',
        'SEC': 'SEC',
        'FTC': 'FTC',
        'EPA': 'EPA',
        'GDPR': 'GDPR',
        'HIPAA': 'HIPAA',
        'PCI': 'PCI',
        'SOC': 'SOC'
    }
    
    found_agencies = []
    for agency_key, agency_name in agencies.items():
        if any(agency_key.lower() in mention.lower() or agency_key.lower() in ctx 
               for mention, ctx in zip(regulatory_mentions, contexts)):
            found_agencies.append(agency_name)
    
    if found_agencies:
        risks.append(
            f"Regulatory oversight identified: {', '.join(found_agencies)} - "
            f"compliance requirements may be significant"
        )
    
    # Check for compliance/approval language
    compliance_keywords = ['approval', 'compliance', 'regulation', 'license', 'permit']
    compliance_mentions = []
    for ctx in contexts:
        for keyword in compliance_keywords:
            if keyword in ctx:
                compliance_mentions.append(keyword)
                break
    
    if compliance_mentions:
        risks.append(
            f"Multiple regulatory requirements mentioned ({len(compliance_mentions)}) - "
            f"may require significant compliance effort and time"
        )
    
    # Check for restrictive language
    restrictive_keywords = ['restrict', 'prohibit', 'ban', 'limit', 'require']
    restrictive_mentions = []
    for ctx in contexts:
        for keyword in restrictive_keywords:
            if keyword in ctx:
                restrictive_mentions.append(keyword)
                break
    
    if restrictive_mentions:
        risks.append(
            f"Restrictive regulatory language found - may limit market entry or operations"
        )
    
    return risks


def analyze_distribution_risks(
    pricing_facts: List[Dict[str, Any]],
    market_size_facts: List[Dict[str, Any]]
) -> List[str]:
    """
    Analyze distribution/channel-specific risks from extracted data.
    
    Args:
        pricing_facts: List of pricing facts
        market_size_facts: List of market size facts
        
    Returns:
        List of specific distribution risk statements
    """
    risks = []
    
    # Analyze pricing data for distribution insights
    if not pricing_facts:
        risks.append(
            "No pricing data found - distribution channel economics cannot be assessed"
        )
    else:
        prices = [f.get('value') for f in pricing_facts if f.get('value') is not None]
        if prices:
            units = [f.get('unit', '').lower() for f in pricing_facts if f.get('unit')]
            
            # Check for pricing variation
            if len(prices) > 1:
                price_range = max(prices) - min(prices)
                avg_price = statistics.mean(prices)
                variation_pct = (price_range / avg_price * 100) if avg_price > 0 else 0
                
                if variation_pct > 100:
                    risks.append(
                        f"Pricing varies significantly ({variation_pct:.1f}% range) - "
                        f"indicates diverse pricing models or market segments, "
                        f"may complicate distribution strategy"
                    )
            
            # Check for low pricing
            min_price = min(prices)
            if 'month' in ' '.join(units):
                if min_price < 10:
                    risks.append(
                        f"Very low pricing found (${min_price:.2f}/month minimum) - "
                        f"may require high volume distribution channels to be viable"
                    )
            elif min_price < 100:
                risks.append(
                    f"Low pricing found (${min_price:.2f} minimum) - "
                    f"may require efficient, low-cost distribution channels"
                )
    
    # Analyze market size for distribution scale requirements
    if market_size_facts:
        values = [f.get('value') for f in market_size_facts if f.get('value') is not None]
        if values:
            # This would need unit normalization, but for now just check if data exists
            risks.append(
                "Market size data available but distribution channel analysis requires "
                "additional data on customer acquisition channels and costs"
            )
    else:
        risks.append(
            "No market size data - cannot assess scale requirements for distribution channels"
        )
    
    return risks

