# Search Services

This package contains the implementations of various web search services that can be used with the MCP Manager.

## Architecture

- **base.py**: Defines the `SearchService` interface and the `SearchResult` data structure
- **perplexity.py**: Implementation of the Perplexity API search service
- **example_service.py**: Example implementation showing how to add a new service
- **search_services_manager.py**: The Search Service Manager that orchestrates all search services

## Adding a New Search Service

1. Create a new file in this package (e.g., `my_service.py`)
2. Implement the `SearchService` interface:

```python
from .base import SearchService, SearchResult

class MySearchService(SearchService):
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        # Implement your search logic here
        results = []
        # ... your implementation ...
        return results
    
    def is_configured(self) -> bool:
        # Check if service is properly configured
        return bool(self.api_key)
    
    def get_service_name(self) -> str:
        return "My Search Service"
```

3. Register the service in `search_services_manager.py`'s `_register_default_services()` method:

```python
def _register_default_services(self):
    from .perplexity import PerplexitySearch
    from .my_service import MySearchService
    
    self.register_search_service("perplexity", PerplexitySearch())
    self.register_search_service("my_service", MySearchService())
    self.set_primary_service("perplexity")
```

## Using the Search Services

The recommended approach is to use the Search Service Manager to get specific services:

```python
from app.services.search.search_services_manager import get_search_service_manager

manager = get_search_service_manager()

# Get a specific service by name
search_service = manager.getService("perplexity")
results = search_service.search("your query here", max_tokens=2000, temperature=0.1)

# Or search directly through the manager
results = manager.search("your query here", service_name="perplexity")

# List all available services
services = manager.list_services()
print(f"Available services: {services}")

# Get service status
status = manager.get_service_status()
for name, info in status.items():
    print(f"{name}: {info}")
```

## Service Parameters

Different search services may accept different parameters. Common parameters include:

- `max_tokens`: Maximum tokens for AI-generated responses (default: 2000)
- `temperature`: Temperature for AI response randomness (default: 0.1)
- Service-specific parameters can be passed as keyword arguments

Example:
```python
search_service = manager.getService("perplexity")
results = search_service.search(
    "your query",
    max_tokens=3000,
    temperature=0.2,
    # service-specific parameters...
)
```
