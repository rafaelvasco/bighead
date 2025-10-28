"""Document model for storing document metadata and content."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Document:
    """
    Document model representing ingested documents in the system.

    Attributes:
        id: Unique identifier for the document
        filename: Original filename of the document
        content: Full text content of the document
        summary: AI-generated summary of the document
        word_count: Total number of words in the document
        line_count: Total number of lines in the document
        chunk_count: Number of chunks created for RAG processing
        created_at: Timestamp when the document was created
        updated_at: Timestamp when the document was last updated
    """
    id: str
    filename: str
    content: str
    summary: Optional[str] = None
    word_count: Optional[int] = None
    line_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Document':
        """Create a Document instance from a dictionary."""
        return cls(
            id=data['id'],
            filename=data['filename'],
            content=data['content'],
            summary=data.get('summary'),
            word_count=data.get('word_count'),
            line_count=data.get('line_count'),
            chunk_count=data.get('chunk_count'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_dict(self) -> dict:
        """Convert Document instance to a dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'content': self.content,
            'summary': self.summary,
            'word_count': self.word_count,
            'line_count': self.line_count,
            'chunk_count': self.chunk_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
