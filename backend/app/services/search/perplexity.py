"""Perplexity AI search service implementation."""

import logging
import os
from typing import List
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import SearchService, SearchResult

logger = logging.getLogger(__name__)


class PerplexitySearch(SearchService):
    """Search service using Perplexity API for comprehensive web search with retry logic."""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar-pro"  # Recommended model for search
        self.request_timeout = 30  # 30 second timeout for requests
        self.max_retries = 3
    
    def is_configured(self) -> bool:
        """Check if the Perplexity API key is configured."""
        return bool(self.api_key)
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "Perplexity API"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
    )
    def _make_request(self, headers: dict, payload: dict) -> dict:
        """Make HTTP request with retry logic."""
        start_time = time.time()
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=self.request_timeout)
        elapsed_time = time.time() - start_time
        
        if elapsed_time > self.request_timeout * 0.8:  # Warn if taking more than 80% of timeout
            logger.warning(f"Perplexity API request took {elapsed_time:.2f}s (close to timeout of {self.request_timeout}s)")
        
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Perform a web search using Perplexity API with retry logic.
        
        Args:
            query: Search query string
            **kwargs: Additional parameters (max_tokens, temperature)
            
        Returns:
            List of search results with comprehensive AI-generated answers
            Empty list if search fails (e.g., unauthorized API key)
        """
        logger.info(f"Performing Perplexity search: {query[:100]}...")
        
        if not self.is_configured():
            logger.warning("Perplexity API key not configured")
            return []  # Return empty list when not configured
        
        try:
            # Extract optional parameters
            max_tokens = kwargs.get('max_tokens', 2000)
            temperature = kwargs.get('temperature', 0.1)
            
            # Craft a comprehensive query for detailed answers
            search_query = self._craft_search_query(query)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": search_query
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Use retry logic for the request
            try:
                data = self._make_request(headers, payload)
            except requests.exceptions.HTTPError as e:
                # Don't retry HTTP errors (400, 401, etc.) as they're likely config issues
                if e.response.status_code == 401:
                    logger.error(f"Perplexity API unauthorized: Invalid API key")
                else:
                    logger.error(f"HTTP error in Perplexity search: {str(e)}")
                return []
            
            return self._parse_response(data, query)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error performing Perplexity search after retries: {str(e)}")
            return []  # Return empty list for request errors
        except Exception as e:
            logger.error(f"Unexpected error in Perplexity search: {str(e)}", exc_info=True)
            raise
    
    def _craft_search_query(self, original_query: str) -> str:
        """Craft a query that will return comprehensive, ready-to-use text."""
        return (
            f"Search for and provide comprehensive information about: {original_query}. "
            "Provide detailed, well-structured information that answers the query thoroughly. "
            "Include relevant facts, context, and key points in a format suitable for creating a document. "
            "Organize the information logically with clear sections and important details highlighted."
        )
    
    def _parse_response(self, data: dict, original_query: str) -> List[SearchResult]:
        """Parse Perplexity API response into SearchResult objects."""
        content = ""
        citations = []
        
        # Extract the content from Perplexity's response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
        
        # Extract citations if available
        if "citations" in data:
            citations = data["citations"]
        
        # Create results list
        results = []
        
        if content:
            # Create a main result with the generated content
            results.append(SearchResult(
                title=f"Comprehensive Answer: {original_query}",
                content=content,
                url="",
                is_generated=True,
                citations=citations
            ))
            
            # Add citation sources if available
            for i, citation in enumerate(citations[:4], 1):  # Limit to 4 citations
                results.append(SearchResult(
                    title=f"Source {i}",
                    content="Reference source from the search results",
                    url=citation,
                    metadata={"is_citation": True}
                ))
        else:
            # Fallback to search results if available
            if "search_results" in data:
                for item in data["search_results"][:5]:
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        content=item.get("snippet", ""),
                        url=item.get("url", "")
                    ))
            else:
                logger.warning("No content could be generated for this search query")
                return []
        
        logger.info(f"Generated {len(results)} results for Perplexity search")
        return results
    
    def _create_error_result(self, error_msg: str = None) -> SearchResult:
        """Create an error search result."""
        if error_msg is None:
            error_msg = "Please set PERPLEXITY_API_KEY in your .env file to enable web search."
            
        return SearchResult(
            title="Search Error",
            content=f"Error performing search: {error_msg}",
            url=""
        )
