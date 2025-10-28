"""Text chunking utilities for semantic and line-based splitting strategies."""
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TextChunker:
    """Provides various strategies for splitting text into chunks."""
    
    def split_text_with_overlap(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap to preserve context across boundaries.
        
        Args:
            text: Text to split
            chunk_size: Size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of chunks with text and line range info
        """
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start_line = 1
        current_line = 1
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            # If adding this line would exceed chunk size, save current chunk
            if current_size + line_length > chunk_size and current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'line_start': chunk_start_line,
                    'line_end': current_line - 1
                })
                
                # Start new chunk with overlap (preserve last few lines)
                overlap_chunk = []
                overlap_size = 0
                overlap_line_start = current_line
                
                # Work backwards from the current position to create overlap
                for i in range(len(current_chunk) - 1, -1, -1):
                    overlap_line = current_chunk[i]
                    overlap_length = len(overlap_line) + 1
                    if overlap_size + overlap_length <= overlap:
                        overlap_chunk.insert(0, overlap_line)
                        overlap_size += overlap_length
                        overlap_line_start -= 1
                    else:
                        break
                
                current_chunk = overlap_chunk
                current_size = overlap_size
                chunk_start_line = overlap_line_start
            
            current_chunk.append(line)
            current_size += line_length
            current_line += 1
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'line_start': chunk_start_line,
                'line_end': current_line - 1
            })
        
        return chunks
    
    def split_text_semantically(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks while preserving semantic coherence.
        For resumes and similar documents, we want to keep related sections together.
        
        Args:
            text: Text to split
            
        Returns:
            List of chunks with text and line range info
        """
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start_line = 1
        current_line = 1
        chunk_size = 800  # Larger chunks for better context
        overlap = 100
        
        # Define section markers that indicate a new semantic unit
        section_markers = [
            "---",  # Markdown section separator
            "###",  # Markdown header
            "##",   # Markdown subheader
            "#",    # Markdown main header
        ]
        
        def is_section_start(line: str) -> bool:
            """Check if a line starts a new section"""
            line_stripped = line.strip()
            for marker in section_markers:
                if line_stripped.startswith(marker):
                    return True
            return False
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            # Start new chunk if this is a section marker and we have content
            if is_section_start(line) and current_chunk and not line.strip() == "":
                # Finish current chunk
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'line_start': chunk_start_line,
                    'line_end': current_line - 1
                })
                
                # Start new chunk without overlap for sections
                current_chunk = [line]
                current_size = line_length
                chunk_start_line = current_line
            # Also split if chunk is getting too big
            elif current_size + line_length > chunk_size and current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'line_start': chunk_start_line,
                    'line_end': current_line - 1
                })
                
                # Start new chunk with overlap (preserve last few lines)
                overlap_chunk = []
                overlap_size = 0
                overlap_line_start = current_line
                
                # Work backwards from the current position to create overlap
                for i in range(len(current_chunk) - 1, -1, -1):
                    overlap_line = current_chunk[i]
                    overlap_length = len(overlap_line) + 1
                    if overlap_size + overlap_length <= overlap:
                        overlap_chunk.insert(0, overlap_line)
                        overlap_size += overlap_length
                        overlap_line_start -= 1
                    else:
                        break
                
                current_chunk = overlap_chunk
                current_size = overlap_size
                chunk_start_line = overlap_line_start
                current_chunk.append(line)
                current_size += line_length
            else:
                current_chunk.append(line)
                current_size += line_length
            
            current_line += 1
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'line_start': chunk_start_line,
                'line_end': current_line - 1
            })
        
        # If we got too many small chunks, merge some of them
        if len(chunks) > 20:  # Too many chunks is usually bad for retrieval
            return self.split_text_with_overlap(text, 1200, 150)  # Fallback to larger chunks
        
        return chunks
    
    def split_text_with_lines(self, text: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """Split text into chunks while tracking line numbers"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start_line = 1
        current_line = 1

        for line in lines:
            line_length = len(line) + 1  # +1 for newline

            # If adding this line would exceed chunk size, save current chunk
            if current_size + line_length > chunk_size and current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'line_start': chunk_start_line,
                    'line_end': current_line - 1
                })
                current_chunk = []
                current_size = 0
                chunk_start_line = current_line

            current_chunk.append(line)
            current_size += line_length
            current_line += 1

        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'line_start': chunk_start_line,
                'line_end': current_line - 1
            })

        return chunks
