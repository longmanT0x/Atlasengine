"""
Text Extraction Module

Extracts clean text from web pages.

Design Decisions:
- Uses BeautifulSoup for HTML parsing
- Removes scripts, styles, and navigation elements
- Extracts main content only
- Handles errors gracefully
"""

from typing import Optional
import httpx
from bs4 import BeautifulSoup
import re


async def extract_clean_text(url: str, timeout: int = 10) -> Optional[str]:
    """
    Extract clean text content from a web page.
    
    Args:
        url: URL of the web page
        timeout: Request timeout in seconds
        
    Returns:
        Clean text content or None if extraction fails
    """
    try:
        # Fetch the page
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            html = response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
    
    try:
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
            soup.find('body')
        )
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limit text length (keep first 50000 characters)
        if len(text) > 50000:
            text = text[:50000] + "..."
        
        return text if text else None
        
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return None

