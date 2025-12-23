"""
Competitor Analysis Module

Analyzes competitors from extracted data and infers positioning.
"""

from typing import List, Dict, Any
import re
from collections import defaultdict


def infer_positioning(context: str, competitor_name: str) -> str:
    """
    Infer competitor positioning from context sentence.
    
    Args:
        context: Context sentence mentioning the competitor
        competitor_name: Name of the competitor
        
    Returns:
        Positioning description
    """
    context_lower = context.lower()
    competitor_lower = competitor_name.lower()
    
    # Look for positioning keywords
    positioning_keywords = {
        'enterprise': ['enterprise', 'large', 'fortune', 'enterprise-grade'],
        'mid-market': ['mid-market', 'mid-market', 'medium', 'sme'],
        'small business': ['small business', 'sme', 'startup', 'small company'],
        'consumer': ['consumer', 'b2c', 'retail', 'individual'],
        'premium': ['premium', 'high-end', 'luxury', 'expensive'],
        'budget': ['budget', 'low-cost', 'affordable', 'cheap', 'economy'],
        'saas': ['saas', 'software-as-a-service', 'cloud', 'subscription'],
        'on-premise': ['on-premise', 'on-premises', 'self-hosted'],
        'vertical': ['vertical', 'industry-specific', 'niche'],
        'horizontal': ['horizontal', 'cross-industry', 'general-purpose']
    }
    
    positioning = []
    for pos_type, keywords in positioning_keywords.items():
        if any(keyword in context_lower for keyword in keywords):
            positioning.append(pos_type)
    
    if positioning:
        return ', '.join(positioning[:2])  # Limit to 2 most relevant
    else:
        return 'General market'


def infer_differentiation(context: str, competitor_name: str) -> str:
    """
    Infer competitor differentiation from context sentence.
    
    Args:
        context: Context sentence mentioning the competitor
        competitor_name: Name of the competitor
        
    Returns:
        Differentiation description
    """
    context_lower = context.lower()
    
    # Look for differentiation keywords
    differentiation_keywords = {
        'price': ['price', 'pricing', 'cost', 'affordable', 'expensive', 'cheap'],
        'features': ['feature', 'functionality', 'capability', 'tool'],
        'integration': ['integration', 'integrate', 'api', 'connect'],
        'ease of use': ['easy', 'simple', 'user-friendly', 'intuitive'],
        'scale': ['scale', 'scalable', 'enterprise', 'large'],
        'speed': ['fast', 'speed', 'performance', 'quick'],
        'security': ['security', 'secure', 'compliance', 'encryption'],
        'support': ['support', 'customer service', 'help', 'service'],
        'brand': ['brand', 'reputation', 'trusted', 'established']
    }
    
    differentiation = []
    for diff_type, keywords in differentiation_keywords.items():
        if any(keyword in context_lower for keyword in keywords):
            differentiation.append(diff_type)
    
    if differentiation:
        return ', '.join(differentiation[:2])  # Limit to 2 most relevant
    else:
        return 'Standard offering'


def extract_pricing_from_context(context: str) -> str:
    """
    Extract pricing information from context if mentioned.
    
    Args:
        context: Context sentence
        
    Returns:
        Pricing description or "Not specified"
    """
    # Look for pricing patterns
    price_patterns = [
        r'\$[\d,]+\.?\d*\s*(?:per\s+)?(?:month|year|user|license)',
        r'[\d,]+\.?\d*\s*(?:per\s+)?(?:month|year|user|license)',
        r'(?:free|freemium|paid|subscription)',
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return "Not specified"


def extract_geography_from_context(context: str) -> str:
    """
    Extract geography information from context if mentioned.
    
    Args:
        context: Context sentence
        
    Returns:
        Geography description or "Not specified"
    """
    geography_keywords = [
        'north america', 'europe', 'asia', 'global', 'us', 'usa', 'uk',
        'canada', 'australia', 'germany', 'france', 'japan', 'china'
    ]
    
    context_lower = context.lower()
    for geo in geography_keywords:
        if geo in context_lower:
            return geo.title()
    
    return "Not specified"


def analyze_competitors(competitor_facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze competitors and aggregate information.
    
    Args:
        competitor_facts: List of competitor facts from extraction
        
    Returns:
        List of competitor analysis dictionaries with:
        - name: Competitor name
        - positioning: Inferred positioning
        - pricing: Pricing information if available
        - geography: Geography if mentioned
        - differentiator: Key differentiators
        - source_url: Source URL
        - mention_count: Number of times mentioned
    """
    # Group by competitor name
    competitor_data = defaultdict(lambda: {
        'name': '',
        'contexts': [],
        'sources': set()
    })
    
    for fact in competitor_facts:
        competitor_name = fact.get('value', '').strip()
        if not competitor_name or len(competitor_name) < 2:
            continue
        
        # Normalize competitor name (capitalize first letter)
        competitor_name = competitor_name.title()
        
        competitor_data[competitor_name]['name'] = competitor_name
        competitor_data[competitor_name]['contexts'].append(
            fact.get('context_sentence', '')
        )
        competitor_data[competitor_name]['sources'].add(
            fact.get('source_url', '')
        )
    
    # Analyze each competitor
    competitors = []
    for name, data in competitor_data.items():
        contexts = data['contexts']
        all_context = ' '.join(contexts)
        
        # Infer positioning from all contexts
        positioning = infer_positioning(all_context, name)
        
        # Infer differentiation
        differentiator = infer_differentiation(all_context, name)
        
        # Extract pricing (from first context with pricing)
        pricing = "Not specified"
        for context in contexts:
            price_info = extract_pricing_from_context(context)
            if price_info != "Not specified":
                pricing = price_info
                break
        
        # Extract geography
        geography = "Not specified"
        for context in contexts:
            geo_info = extract_geography_from_context(context)
            if geo_info != "Not specified":
                geography = geo_info
                break
        
        # Get source URL (use first source)
        source_url = list(data['sources'])[0] if data['sources'] else ''
        
        competitors.append({
            'name': name,
            'positioning': positioning,
            'pricing': pricing,
            'geography': geography,
            'differentiator': differentiator,
            'source_url': source_url,
            'mention_count': len(contexts)
        })
    
    # Sort by mention count (most mentioned first)
    competitors.sort(key=lambda x: x['mention_count'], reverse=True)
    
    return competitors

