"""
Search Module

Handles web search using DuckDuckGo (no API key required).

Design Decisions:
- Uses DuckDuckGo for privacy and no API key requirement
- Implements rate limiting to avoid being blocked
- Returns structured search results
"""

from typing import List, Dict, Any
import time
from duckduckgo_search import DDGS


def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search DuckDuckGo for a given query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, url, and snippet
    """
    try:
        with DDGS() as ddgs:
            results = []
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
            return results
    except Exception as e:
        # If search fails, return empty list
        print(f"DuckDuckGo search error: {e}")
        return []


def search_multiple_queries(queries: List[str], max_results_per_query: int = 10) -> List[Dict[str, Any]]:
    """
    Execute multiple search queries and combine results.
    
    Args:
        queries: List of search query strings
        max_results_per_query: Maximum results per query
        
    Returns:
        Combined list of search results (may contain duplicates)
    """
    all_results = []
    for query in queries:
        results = search_duckduckgo(query, max_results=max_results_per_query)
        all_results.extend(results)
        # Small delay between queries to avoid rate limiting
        time.sleep(0.5)
    
    return all_results

