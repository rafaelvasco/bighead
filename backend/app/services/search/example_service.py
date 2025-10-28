"""Example of implementing a new search service."""

import logging
from typing import List

from .base import SearchService, SearchResult

logger = logging.getLogger(__name__)


class ExampleSearchService(SearchService):
    """Example search service that demonstrates the interface."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key)
    
    def get_service_name(self) -> str:
        """Get the service name."""
        return "Example Search"
    
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Perform a search using the example service.
        
        Args:
            query: Search query string
            **kwargs: Additional parameters (e.g., num_results)
            
        Returns:
            List of search results
        """
        if not self.is_configured():
            logger.warning("Example search service not configured")
            return [SearchResult(
                title="Service Not Configured",
                content="Please provide an API key for ExampleSearch",
                url=""
            )]
        
        # Implementation would go here
        # For now, return a mock result
        return [SearchResult(
            title=f"Example result for: {query}",
            content="This is a mock result from the example search service.",
            url="https://example.com",
            metadata={"source": "ExampleSearch"}
        )]


# To register this service, add to search_services_manager.py's _register_default_services:
#
# def _register_default_services(self):
#     from .perplexity import PerplexitySearch
#     from .example_service import ExampleSearchService
#     
#     self.register_search_service("perplexity", PerplexitySearch())
#     self.register_search_service("example", ExampleSearchService(api_key="your_key"))
#     self.set_primary_service("perplexity")
