"""
web_search.py — Real-time Web Search Integration for Inez
===========================================================
Integrates Brave Search API to provide real-time web search
capabilities with source citations for ArchonHub agents.
"""

from __future__ import annotations

import os
import json
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    requests = None

try:
    from ah_logging import get_logger
    logger = get_logger("web_search")
except Exception:
    import logging
    logger = logging.getLogger("web_search")


@dataclass
class SearchSource:
    """Represents a single search result source."""
    id: int
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    source_type: str = "web"  # web, document, memory
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SearchResult:
    """Complete search result with sources and formatted response."""
    query: str
    sources: List[SearchSource]
    search_timestamp: str
    num_results: int
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "sources": [s.to_dict() for s in self.sources],
            "search_timestamp": self.search_timestamp,
            "num_results": self.num_results
        }


class BraveSearchClient:
    """Client for Brave Search API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY", "")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    def search(
        self,
        query: str,
        num_results: int = 5,
        search_lang: str = "en",
        country: str = "us"
    ) -> SearchResult:
        """
        Perform a web search using Brave Search API.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 20)
            search_lang: Language code (default: "en")
            country: Country code (default: "us")
            
        Returns:
            SearchResult object with sources
            
        Raises:
            Exception: If API call fails or no API key configured
        """
        if not self.api_key:
            raise ValueError("Brave Search API key not configured. Set BRAVE_API_KEY environment variable.")
        
        if not REQUESTS_OK:
            raise ImportError("requests library not available")
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": min(num_results, 20),
            "text_decorations": True,
            "search_lang": search_lang,
            "country": country
        }
        
        try:
            logger.info(f"🌐 Searching Brave: '{query}' (limit={num_results})")
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            sources = []
            web_results = data.get("web", {}).get("results", [])
            
            for i, result in enumerate(web_results[:num_results], 1):
                source = SearchSource(
                    id=i,
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("description", ""),
                    published_date=result.get("age"),
                    source_type="web"
                )
                sources.append(source)
            
            search_result = SearchResult(
                query=query,
                sources=sources,
                search_timestamp=datetime.utcnow().isoformat() + "Z",
                num_results=len(sources)
            )
            
            logger.info(f"✅ Found {len(sources)} results for '{query}'")
            return search_result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("🚫 Brave Search API: Invalid API key")
                raise ValueError("Invalid Brave Search API key")
            elif e.response.status_code == 429:
                logger.error("⏱️ Brave Search API: Rate limit exceeded")
                raise ValueError("Brave Search rate limit exceeded")
            else:
                logger.error(f"❌ Brave Search API error: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise


class SearchAnalyzer:
    """Analyzes queries to determine if web search is needed."""
    
    # Patterns that indicate web search would be helpful
    SEARCH_PATTERNS = [
        r'\b(?:latest|recent|current|today|this week|breaking|news about)\b',
        r'\b(?:what is|what are|what\'s)\b.{0,50}\b(?:happening|going on|trending)\b',
        r'\b(?:price|stock|market|trading) (?:of|for)\b',
        r'\b(?:weather|temperature) in\b',
        r'\b(?:how much|cost) (?:is|does)\b',
        r'\b(?:find|search for|look up|get info about)\b',
        r'\b(?:when is|when will|when did)\b.{0,50}\b(?:next|upcoming)\b',
        r'\b(?:status|state|condition) of\b',
        r'\b(?:compare|versus|vs\.?) ',
    ]
    
    # Topics that usually need fresh data
    FRESH_DATA_TOPICS = [
        "market", "stock", "price", "trading", "earnings",
        "news", "weather", "sports", "election",
        "covid", "virus", "outbreak",
        "breaking", "latest", "current", "recent"
    ]
    
    @classmethod
    def should_search(cls, query: str) -> bool:
        """
        Determine if a query would benefit from web search.
        
        Args:
            query: User's query string
            
        Returns:
            True if web search should be performed
        """
        query_lower = query.lower()
        
        # Check patterns
        for pattern in cls.SEARCH_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True
        
        # Check topics
        for topic in cls.FRESH_DATA_TOPICS:
            if topic in query_lower:
                return True
        
        return False


class CitationFormatter:
    """Formats LLM responses with inline citations."""
    
    @staticmethod
    def format_with_citations(text: str, sources: List[SearchSource]) -> str:
        """
        Add citation footer to response text.
        
        Args:
            text: Response text (may contain [cite:N] markers)
            sources: List of SearchSource objects
            
        Returns:
            Formatted text with citation footer
        """
        if not sources:
            return text
        
        # Replace [cite:N] markers with [N]
        formatted = text
        for i in range(1, len(sources) + 1):
            formatted = formatted.replace(f"[cite:{i}]", f"[{i}]")
        
        # Add source footer
        formatted += "\n\n**Sources:**\n"
        for source in sources:
            date_str = f" ({source.published_date})" if source.published_date else ""
            formatted += f"[{source.id}] {source.title}{date_str}\n    {source.url}\n"
        
        return formatted
    
    @staticmethod
    def extract_citations_metadata(text: str) -> Dict[str, Any]:
        """
        Extract citation metadata from formatted text.
        
        Returns dict with 'has_citations' and 'citation_ids' fields.
        """
        citations = re.findall(r'\[(\d+)\]', text)
        return {
            "has_citations": len(citations) > 0,
            "citation_ids": list(set(map(int, citations)))
        }


def format_search_context_for_llm(search_result: SearchResult) -> str:
    """
    Format search results as context for LLM prompt.
    
    Args:
        search_result: SearchResult object
        
    Returns:
        Formatted string for LLM context
    """
    if not search_result.sources:
        return ""
    
    lines = [
        f"Web search results for: \"{search_result.query}\"",
        f"(Retrieved: {search_result.search_timestamp})",
        ""
    ]
    
    for source in search_result.sources:
        date_str = f" [{source.published_date}]" if source.published_date else ""
        lines.append(f"[{source.id}] {source.title}{date_str}")
        lines.append(f"    {source.snippet}")
        lines.append(f"    Source: {source.url}")
        lines.append("")
    
    lines.append("Instructions:")
    lines.append("- Use these sources to provide accurate, up-to-date information")
    lines.append("- Cite sources inline using [cite:N] where N is the source number")
    lines.append("- If sources don't fully answer the question, supplement with your knowledge")
    lines.append("")
    
    return "\n".join(lines)


# ── Example usage ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test search
    client = BraveSearchClient()
    
    query = "Tesla stock price today"
    result = client.search(query, num_results=3)
    
    print(f"Query: {result.query}")
    print(f"Found {result.num_results} results:\n")
    
    for source in result.sources:
        print(f"[{source.id}] {source.title}")
        print(f"    {source.snippet}")
        print(f"    {source.url}\n")
    
    # Test analyzer
    print("\nSearch analysis:")
    print(f"  'Tesla stock today' -> {SearchAnalyzer.should_search('Tesla stock today')}")
    print(f"  'What is 2+2?' -> {SearchAnalyzer.should_search('What is 2+2?')}")
    print(f"  'Latest news about AI' -> {SearchAnalyzer.should_search('Latest news about AI')}")
