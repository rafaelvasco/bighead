"""Chat history model for storing conversation messages."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ChatHistory:
    """
    Chat history model representing messages in document conversations.

    Attributes:
        id: Auto-incrementing message ID
        document_id: Foreign key to the associated document
        sender: Who sent the message ('human' or 'ai')
        message: The text content of the message
        sources: Optional list of source chunks used to generate AI responses
        created_at: Timestamp when the message was created
    """
    id: int
    document_id: str
    sender: str
    message: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ChatHistory':
        """Create a ChatHistory instance from a dictionary."""
        return cls(
            id=data['id'],
            document_id=data['document_id'],
            sender=data['sender'],
            message=data['message'],
            sources=data.get('sources'),
            created_at=data.get('created_at')
        )

    def to_dict(self) -> dict:
        """Convert ChatHistory instance to a dictionary."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'sender': self.sender,
            'message': self.message,
            'sources': self.sources,
            'created_at': self.created_at
        }
