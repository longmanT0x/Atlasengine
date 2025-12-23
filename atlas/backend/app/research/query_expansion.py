"""
Query Expansion Module

Expands user ideas into multiple search queries for comprehensive research.

Design Decisions:
- Creates multiple query variations to capture different aspects
- Includes industry-specific, market-size, and competitive queries
- Uses different query structures to maximize coverage
"""

from typing import List


def expand_idea_into_queries(
    idea: str,
    industry: str,
    geography: str,
    customer_type: str
) -> List[str]:
    """
    Expand a user idea into multiple search queries.
    
    Creates queries covering:
    - Market size and growth
    - Industry trends
    - Competitive landscape
    - Customer segments
    - Geographic market data
    
    Args:
        idea: User's startup idea description
        industry: Industry classification
        geography: Target geography
        customer_type: Type of customers
        
    Returns:
        List of search query strings
    """
    queries = []
    
    # Base queries about the idea and industry
    queries.append(f"{idea} {industry} market size")
    queries.append(f"{industry} market size {geography}")
    queries.append(f"{idea} {industry} growth trends")
    
    # Market research queries
    queries.append(f"{industry} market research {geography}")
    queries.append(f"{customer_type} {industry} market {geography}")
    queries.append(f"{industry} industry report {geography}")
    
    # Competitive landscape
    queries.append(f"{idea} competitors {industry}")
    queries.append(f"{industry} competitive landscape {geography}")
    
    # Industry statistics and data
    queries.append(f"{industry} statistics {geography}")
    queries.append(f"{industry} market analysis {geography}")
    
    return queries

