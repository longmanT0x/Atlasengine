"""
Extraction Patterns Module

Conservative regex patterns for extracting structured data from text.

Design Decisions:
- Patterns are conservative - only match explicit, clear statements
- Avoids speculative extraction
- Requires context keywords to ensure relevance
- Handles various number formats and units
"""

import re
from typing import List, Dict, Optional, Tuple, Any


def extract_market_size(text: str) -> List[Dict[str, Any]]:
    """
    Extract market size figures from text.
    
    Looks for patterns like:
    - "market size of $X billion"
    - "market valued at $X"
    - "TAM of $X"
    - "market worth $X"
    
    Args:
        text: Text to search
        
    Returns:
        List of dictionaries with value, unit, and context
    """
    results = []
    
    # Pattern for market size with explicit keywords
    # Matches: "market size of $5.2 billion", "TAM of $10B", "market valued at $500M"
    patterns = [
        # Market size with dollar amounts
        r'(?:market\s+size|TAM|total\s+addressable\s+market|market\s+valued|market\s+worth|market\s+value)\s+(?:of|is|at|:)?\s*\$?\s*([\d,]+\.?\d*)\s*([BMK]|billion|million|trillion|thousand)',
        # Market size with explicit "billion/million" after number
        r'\$?\s*([\d,]+\.?\d*)\s*(billion|million|trillion|thousand)\s+(?:dollar|USD)?\s+(?:market|TAM|industry)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(',', '')
            unit_str = match.group(2).upper()
            
            try:
                value = float(value_str)
                
                # Normalize units to standard form
                unit_map = {
                    'B': 'billion', 'BILLION': 'billion',
                    'M': 'million', 'MILLION': 'million',
                    'K': 'thousand', 'THOUSAND': 'thousand',
                    'T': 'trillion', 'TRILLION': 'trillion'
                }
                unit = unit_map.get(unit_str, unit_str.lower())
                
                # Get context sentence
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                # Extract sentence containing the match
                sentence_match = re.search(r'[.!?]\s*[^.!?]*' + re.escape(match.group(0)) + r'[^.!?]*[.!?]', 
                                          text[max(0, start-200):end+200])
                if sentence_match:
                    context = sentence_match.group(0).strip()
                
                results.append({
                    'value': value,
                    'unit': unit,
                    'context': context
                })
            except ValueError:
                continue
    
    return results


def extract_growth_rates(text: str) -> List[Dict[str, Any]]:
    """
    Extract growth rate figures from text.
    
    Looks for patterns like:
    - "growing at X%"
    - "growth rate of X%"
    - "CAGR of X%"
    - "annual growth of X%"
    
    Args:
        text: Text to search
        
    Returns:
        List of dictionaries with value, unit, and context
    """
    results = []
    
    # Pattern for growth rates with explicit keywords
    patterns = [
        # Growth rate with percentage
        r'(?:growth\s+rate|CAGR|compound\s+annual\s+growth|annual\s+growth|growing\s+at|grows\s+at)\s+(?:of|is|:)?\s*([\d,]+\.?\d*)\s*%',
        # Percentage followed by growth keywords
        r'([\d,]+\.?\d*)\s*%\s+(?:growth|CAGR|annual\s+growth)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(',', '')
            
            try:
                value = float(value_str)
                
                # Get context sentence
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                # Extract sentence containing the match
                sentence_match = re.search(r'[.!?]\s*[^.!?]*' + re.escape(match.group(0)) + r'[^.!?]*[.!?]', 
                                          text[max(0, start-200):end+200])
                if sentence_match:
                    context = sentence_match.group(0).strip()
                
                results.append({
                    'value': value,
                    'unit': 'percent',
                    'context': context
                })
            except ValueError:
                continue
    
    return results


def extract_pricing(text: str) -> List[Dict[str, Any]]:
    """
    Extract pricing references from text.
    
    Looks for patterns like:
    - "priced at $X"
    - "costs $X"
    - "subscription of $X"
    - "price point of $X"
    
    Args:
        text: Text to search
        
    Returns:
        List of dictionaries with value, unit, and context
    """
    results = []
    
    # Pattern for pricing with explicit keywords
    patterns = [
        # Pricing with dollar amounts
        r'(?:price|priced|costs?|subscription|fee|pricing)\s+(?:of|at|is|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(?:per\s+(?:month|year|user|license))?',
        # Dollar amount followed by pricing keywords
        r'\$?\s*([\d,]+\.?\d*)\s+(?:per\s+)?(?:month|year|user|license|subscription)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1).replace(',', '')
            
            try:
                value = float(value_str)
                
                # Determine unit from context
                unit = 'USD'
                if 'per month' in match.group(0).lower() or 'monthly' in match.group(0).lower():
                    unit = 'USD per month'
                elif 'per year' in match.group(0).lower() or 'annual' in match.group(0).lower():
                    unit = 'USD per year'
                elif 'per user' in match.group(0).lower():
                    unit = 'USD per user'
                
                # Get context sentence
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                # Extract sentence containing the match
                sentence_match = re.search(r'[.!?]\s*[^.!?]*' + re.escape(match.group(0)) + r'[^.!?]*[.!?]', 
                                          text[max(0, start-200):end+200])
                if sentence_match:
                    context = sentence_match.group(0).strip()
                
                results.append({
                    'value': value,
                    'unit': unit,
                    'context': context
                })
            except ValueError:
                continue
    
    return results


def extract_competitors(text: str) -> List[Dict[str, Any]]:
    """
    Extract competitor names from text.
    
    Looks for patterns like:
    - "competitors include X, Y, Z"
    - "competing with X"
    - "rivals such as X"
    
    Args:
        text: Text to search
        
    Returns:
        List of dictionaries with competitor name and context
    """
    results = []
    
    # Pattern for competitor mentions
    patterns = [
        # Competitors include/list
        r'(?:competitors?|rivals?|competition)\s+(?:include|includes|such\s+as|like|are|is)\s+([A-Z][A-Za-z\s&,]+?)(?:\.|,|\s+and|\s+or)',
        # Competing with
        r'competing\s+(?:with|against)\s+([A-Z][A-Za-z\s&]+?)(?:\.|,|\s+and)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            competitors_str = match.group(1)
            
            # Split multiple competitors
            competitors = re.split(r',|\s+and\s+|\s+or\s+', competitors_str)
            
            for competitor in competitors:
                competitor = competitor.strip()
                # Filter out common words and short names
                if len(competitor) > 2 and competitor.lower() not in ['the', 'a', 'an', 'and', 'or']:
                    # Get context sentence
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    # Extract sentence containing the match
                    sentence_match = re.search(r'[.!?]\s*[^.!?]*' + re.escape(match.group(0)) + r'[^.!?]*[.!?]', 
                                              text[max(0, start-200):end+200])
                    if sentence_match:
                        context = sentence_match.group(0).strip()
                    
                    results.append({
                        'value': competitor,
                        'unit': None,
                        'context': context
                    })
    
    return results


def extract_regulatory_mentions(text: str) -> List[Dict[str, Any]]:
    """
    Extract regulatory mentions from text.
    
    Looks for patterns like:
    - "FDA approval"
    - "regulated by X"
    - "compliance with X"
    - "regulatory requirements"
    
    Args:
        text: Text to search
        
    Returns:
        List of dictionaries with regulatory mention and context
    """
    results = []
    
    # Pattern for regulatory mentions
    patterns = [
        # Regulatory agencies and requirements
        r'(?:FDA|SEC|FTC|EPA|regulatory|regulation|compliance|approval|license)\s+(?:approval|requirements?|compliance|oversight|regulation)',
        # Regulated by
        r'regulated\s+by\s+([A-Z][A-Za-z\s]+?)(?:\.|,|\s+and)',
        # Compliance with
        r'compliance\s+with\s+([A-Z][A-Za-z\s]+?)(?:\.|,|\s+and)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get context sentence
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            # Extract sentence containing the match
            sentence_match = re.search(r'[.!?]\s*[^.!?]*' + re.escape(match.group(0)) + r'[^.!?]*[.!?]', 
                                      text[max(0, start-200):end+200])
            if sentence_match:
                context = sentence_match.group(0).strip()
            
            # Extract the regulatory mention
            mention = match.group(0) if match.lastindex is None else match.group(1) or match.group(0)
            
            results.append({
                'value': mention,
                'unit': None,
                'context': context
            })
    
    return results

