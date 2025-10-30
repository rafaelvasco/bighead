"""MCP (Model Context Protocol) Manager for orchestrating search services."""

import logging
from typing import Dict, Any, List, Optional

from .base import SearchService, SearchResult

logger = logging.getLogger(__name__)


class SearchServiceManager:
    """
    Simplified Search Service Manager for managing search services.
    Maintains a registry of available search services while keeping extensibility.
    """
    
    def __init__(self):
        self._search_services: Dict[str, SearchService] = {}
        self._primary_service: Optional[str] = None
        self._register_default_services()
    
    def _register_default_services(self):
        """Register default search services."""
        from .perplexity import PerplexitySearch
        self._search_services["perplexity"] = PerplexitySearch()
        self._primary_service = "perplexity"
    
    def register_search_service(self, name: str, service: SearchService):
        """Register a new search service."""
        self._search_services[name] = service
        logger.info(f"Registered search service: {name}")
    
    def getService(self, name: str = None):
        """Get a specific search service by name (using camelCase for consistency)."""
        if name is None:
            name = self._primary_service
        
        service = self._search_services.get(name)
        if not service:
            raise ValueError(f"Search service '{name}' not found. Available services: {list(self._search_services.keys())}")
        return service
    
    def search(self, query: str, service_name: Optional[str] = None, **kwargs) -> List[SearchResult]:
        """
        Perform a web search using specified or primary service.
        """
        service = self.getService(service_name)
        
        if not service.is_configured():
            service_name_for_logging = service_name or self._primary_service or "unknown"
            logger.error(f"Search service '{service_name_for_logging}' is not configured")
            raise ValueError(f"Search service '{service_name_for_logging}' is not configured")
        
        # Perform the search
        logger.info(f"Performing search using service: {service.get_service_name()}")
        return service.search(query, **kwargs)


# Singleton instance for the application
_search_service_manager = None


def get_search_service_manager() -> SearchServiceManager:
    """Get or create the singleton search service manager instance."""
    global _search_service_manager
    if _search_service_manager is None:
        _search_service_manager = SearchServiceManager()
    return _search_service_manager

