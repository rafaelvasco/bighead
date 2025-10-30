"""Query service for handling RAG query operations."""
import logging
from typing import Dict, Any

from app.database import get_db_service
from app.services.retrieval import get_rag_service
from app.utils.errors import NotFoundError

logger = logging.getLogger(__name__)


class QueryService:
    """Service for managing query operations."""

    def __init__(self):
        self.db = get_db_service()
        self.rag = get_rag_service()

    def query_documents(self, question: str, document_id: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query documents using RAG and save to chat history.

        Args:
            question: The question to ask
            document_id: ID of the document being queried
            top_k: Number of chunks to retrieve

        Returns:
            Dict with answer and sources

        Raises:
            NotFoundError: If document doesn't exist
        """
        logger.debug(f"Processing query for document {document_id}: {question[:50]}...")

        # Verify document exists
        doc = self.db.get_document_by_id(document_id)
        if not doc:
            logger.warning(f"Document not found: {document_id}")
            raise NotFoundError(f"Document with ID {document_id} not found")

        # Query RAG
        try:
            result = self.rag.query(question, top_k)
            logger.info(f"RAG query successful for document {document_id}")
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise

        # Save to chat history (batch both messages in transaction)
        chat_saved = True
        try:
            answer = result.get('answer', '')
            self.db.add_chat_message(document_id, 'human', question)
            self.db.add_chat_message(
                document_id,
                'ai',
                answer,
                result.get('sources', [])
            )
            logger.debug(f"Saved query to chat history for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to save to chat history: {str(e)}")
            chat_saved = False

        # Include persistence status in response
        result['chat_saved'] = chat_saved
        return result


# Singleton instance
_query_service = None


def get_query_service() -> QueryService:
    """Get or create the singleton query service instance."""
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service
