"""Query expansion utilities for improving retrieval effectiveness."""
import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class QueryExpander:
    """Provides query expansion strategies to improve retrieval."""
    
    def expand_temporal_query(self, question: str) -> str:
        """
        Expand temporal queries to improve retrieval by adding relevant terms.
        
        Args:
            question: Original user question
            
        Returns:
            Expanded query with additional relevant terms
        """
        question_lower = question.lower()
        
        # Detect year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        years_found = re.findall(year_pattern, question, re.IGNORECASE)
        
        if len(years_found) >= 2:  # At least two years indicates a range
            # Create flexible variations for common verbs
            terms_to_add = []
            
            # Add alternative ways to express the relationship
            if 'work' in question_lower:
                terms_to_add.extend(['employment', 'job', 'position', 'company'])
            
            # Add temporal indicators
            if any(word in question_lower for word in ['from', 'to', 'until', 'through', 'between', 'during']):
                terms_to_add.extend(['time period', 'duration'])
            
            # If we have terms to add, append them to improve matching
            if terms_to_add:
                # Use the original question with additional context terms
                expanded = f"{question} {' '.join(terms_to_add)}"
                return expanded
        
        return question
