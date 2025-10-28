"""Common interface and data structures for search services."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class SearchResult:
    """Standardized search result structure."""
    
    def __init__(
        self,
        title: str,
        content: str,
        url: str = "",
        is_generated: bool = False,
        citations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.url = url
        self.is_generated = is_generated
        self.citations = citations or []
        self.metadata = metadata or {}


class SearchService(ABC):
    """Interface for all search services."""
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Perform a web search.
        
        Args:
            query: Search query string
            **kwargs: Additional service-specific parameters
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the name of the search service."""
        pass
