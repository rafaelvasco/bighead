"""String utilities for content truncation and processing."""


def truncate_content(content: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate content to a maximum length with optional suffix.
    
    Args:
        content: The string content to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to append if truncated (default "...")
        
    Returns:
        Truncated content or original if shorter than max_length
        
    Example:
        >>> truncate_content("hello world", 5)
        'hello...'
        >>> truncate_content("hi", 5)
        'hi'
    """
    if len(content) > max_length:
        return content[:max_length] + suffix
    return content
