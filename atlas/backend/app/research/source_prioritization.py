"""
Source Prioritization Module

Prioritizes sources based on credibility and type.

Design Decisions:
- Government sources (gov, .gov) are highest priority
- Academic sources (.edu, .ac.uk, etc.) are high priority
- Industry sources (established companies, industry reports) are medium-high
- Blogs and personal sites are lowest priority
- Credibility scores: high, medium, low
"""

from typing import List, Dict, Any
import re


def calculate_credibility_score(url: str, title: str) -> str:
    """
    Calculate credibility score based on URL and title patterns.
    
    Args:
        url: Source URL
        title: Source title
        
    Returns:
        Credibility score: 'high', 'medium', or 'low'
    """
    url_lower = url.lower()
    title_lower = title.lower()
    
    # High credibility indicators
    high_indicators = [
        r'\.gov\b',  # Government sites
        r'\.edu\b',  # Educational institutions
        r'\.ac\.',   # Academic domains (.ac.uk, .ac.jp, etc.)
        r'census\.gov',
        r'bls\.gov',  # Bureau of Labor Statistics
        r'sec\.gov',  # SEC
        r'fda\.gov',
        r'who\.int',
        r'un\.org',
        r'oecd\.org',
        r'worldbank\.org',
        r'imf\.org',
    ]
    
    # Medium credibility indicators
    medium_indicators = [
        r'\.org\b',
        r'statista\.com',
        r'mckinsey\.com',
        r'pwc\.com',
        r'deloitte\.com',
        r'gartner\.com',
        r'forrester\.com',
        r'idc\.com',
        r'gartner\.com',
        r'industry report',
        r'market research',
        r'white paper',
    ]
    
    # Low credibility indicators (blogs, personal sites)
    low_indicators = [
        r'blogspot\.',
        r'wordpress\.com',
        r'medium\.com',
        r'substack\.com',
        r'personal blog',
        r'\.blog\b',
    ]
    
    # Check for high credibility
    for pattern in high_indicators:
        if re.search(pattern, url_lower) or re.search(pattern, title_lower):
            return 'high'
    
    # Check for low credibility
    for pattern in low_indicators:
        if re.search(pattern, url_lower) or re.search(pattern, title_lower):
            return 'low'
    
    # Check for medium credibility
    for pattern in medium_indicators:
        if re.search(pattern, url_lower) or re.search(pattern, title_lower):
            return 'medium'
    
    # Default to medium for unknown sources
    return 'medium'


def prioritize_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize and sort sources by credibility.
    
    Args:
        sources: List of source dictionaries with url, title, snippet
        
    Returns:
        Sorted list of sources (high credibility first)
    """
    # Add credibility scores
    for source in sources:
        source['credibility'] = calculate_credibility_score(
            source.get('url', ''),
            source.get('title', '')
        )
    
    # Sort by credibility (high > medium > low)
    credibility_order = {'high': 0, 'medium': 1, 'low': 2}
    sources.sort(key=lambda x: credibility_order.get(x.get('credibility', 'medium'), 2))
    
    return sources


def filter_high_quality_sources(
    sources: List[Dict[str, Any]],
    min_credibility: str = 'medium',
    max_results: int = 8
) -> List[Dict[str, Any]]:
    """
    Filter sources to get high-quality ones.
    
    Args:
        sources: List of sources with credibility scores
        min_credibility: Minimum credibility level ('high', 'medium', 'low')
        max_results: Maximum number of sources to return
        
    Returns:
        Filtered and limited list of high-quality sources
    """
    credibility_order = {'high': 0, 'medium': 1, 'low': 2}
    min_order = credibility_order.get(min_credibility, 1)
    
    filtered = [
        s for s in sources
        if credibility_order.get(s.get('credibility', 'medium'), 2) <= min_order
    ]
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_sources = []
    for source in filtered:
        url = source.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(source)
            if len(unique_sources) >= max_results:
                break
    
    return unique_sources

