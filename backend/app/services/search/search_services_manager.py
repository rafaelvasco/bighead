"""MCP (Model Context Protocol) Manager for orchestrating search services."""

import logging
from typing import Dict, Any, List, Optional

from .base import SearchService, SearchResult

logger = logging.getLogger(__name__)


class SearchServiceManager:
    """
    Search Service Manager for managing and orchestrating various search services.
    This manager maintains a registry of available search services and delegates
    search requests to the appropriate service.
    """
    
    def __init__(self):
        self._search_services: Dict[str, SearchService] = {}
        self._primary_service: Optional[str] = None
        self._register_default_services()
    
    def _register_default_services(self):
        """Register default search services."""
        from .perplexity import PerplexitySearch
        
        # Register Perplexity
        self.register_search_service("perplexity", PerplexitySearch())
        self.set_primary_service("perplexity")
    
    def register_search_service(self, name: str, service: SearchService):
        """
        Register a new search service.
        
        Args:
            name: Unique name for the service
            service: SearchService instance
        """
        self._search_services[name] = service
        logger.info(f"Registered search service: {name}")
    
    def set_primary_service(self, name: str):
        """
        Set the primary search service to use.
        
        Args:
            name: Name of the service to set as primary
        """
        if name not in self._search_services:
            raise ValueError(f"Search service '{name}' not found")
        self._primary_service = name
        logger.info(f"Set primary search service to: {name}")
    
    def get_primary_service(self) -> Optional[SearchService]:
        """Get the primary search service."""
        if self._primary_service and self._primary_service in self._search_services:
            return self._search_services[self._primary_service]
        return None
    
    def getService(self, name: str):
        """Get a specific search service by name (using camelCase for consistency)."""
        service = self._search_services.get(name)
        if not service:
            raise ValueError(f"Search service '{name}' not found. Available services: {list(self._search_services.keys())}")
        return service
    

    def list_services(self) -> List[str]:
        """List all registered search service names."""
        return list(self._search_services.keys())
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all registered services."""
        status = {}
        for name, service in self._search_services.items():
            status[name] = {
                "name": service.get_service_name(),
                "configured": service.is_configured(),
                "is_primary": name == self._primary_service
            }
        return status
    
    def search(self, query: str, service_name: Optional[str] = None, **kwargs) -> List[SearchResult]:
        """
        Perform a web search using specified or primary service.
        
        Args:
            query: Search query string
            service_name: Optional service name to use (defaults to primary)
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
            
        Raises:
            ValueError: If no service is specified or available
        """
        # Determine which service to use
        if service_name:
            if service_name not in self._search_services:
                raise ValueError(f"Search service '{service_name}' not found")
            service = self._search_services[service_name]
        else:
            service = self.get_primary_service()
            if not service:
                raise ValueError("No primary search service configured")
        
        # Check if service is properly configured
        if not service.is_configured():
            service_name_for_logging = service_name or self._primary_service or "unknown"
            logger.error(f"Search service '{service_name_for_logging}' is not configured")
            raise ValueError(f"Search service '{service_name_for_logging}' is not configured")
        
        # Perform the search
        logger.info(f"Performing search using service: {service.get_service_name()}")
        return service.search(query, **kwargs)
    
    def search_with_context(self, query: str, document_context: str = "", **kwargs) -> Dict[str, Any]:
        """
        Perform a search and return results with relevance to document context.
        
        Args:
            query: Search query
            document_context: Context from the analyzed document (optional)
            **kwargs: Additional search parameters
            
        Returns:
            Search results with metadata
        """
        results = self.search(query, **kwargs)
        
        return {
            "query": query,
            "results": results,
            "context_aware": bool(document_context),
            "result_count": len(results),
            "service_used": self._primary_service or "unknown"
        }


# Singleton instance for the application
_search_service_manager = None


def get_search_service_manager() -> SearchServiceManager:
    """Get or create the singleton search service manager instance."""
    global _search_service_manager
    if _search_service_manager is None:
        _search_service_manager = SearchServiceManager()
    return _search_service_manager

