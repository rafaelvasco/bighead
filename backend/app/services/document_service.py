"""Document service for handling document business logic."""
import logging
from typing import Dict, Any, Optional, List
from werkzeug.datastructures import FileStorage

from app.database import get_db_service
from app.services.retrieval import get_rag_service
from app.services.search.search_services_manager import get_search_service_manager
from app.utils.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document operations."""

    def __init__(self):
        self.db = get_db_service()
        self.rag = get_rag_service()
        self.search_manager = get_search_service_manager()
        logger.info("DocumentService initialized")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in a readable format"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _reindex_document(self, filename: str, content: str, is_new: bool = False) -> int:
        """
        Helper method to reindex a document in RAG and calculate metadata.
        Handles deletion of old chunks (for updates) and indexing of new content.
        
        Args:
            filename: Document filename
            content: Document content
            is_new: Whether this is a new document (skip deletion of old chunks)
            
        Returns:
            Number of chunks created
            
        Raises:
            ValidationError: If indexing fails
        """
        # Only delete old RAG chunks if updating an existing document
        if not is_new:
            try:
                self.rag.delete_document(filename)
            except Exception as e:
                logger.warning(f"Failed to delete old chunks for {filename}: {str(e)}")
        
        # Index in RAG
        try:
            chunk_count = self.rag.index_document(filename, content)
        except Exception as e:
            logger.error(f"Failed to index document {filename}: {str(e)}")
            raise ValidationError(f"Failed to index document: {str(e)}")
        
        return chunk_count

    def upload_document(self, file: FileStorage) -> Dict[str, Any]:
        """
        Upload and index a document.

        Args:
            file: File upload object

        Returns:
            Dict with document info and upload status

        Raises:
            ValidationError: If file cannot be read or processed
        """
        filename = file.filename

        # Read file content
        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {filename}: {str(e)}")
            raise ValidationError("File must be valid UTF-8 encoded text")

        # Check if document exists
        existing_doc = self.db.get_document_by_filename(filename)
        is_update = existing_doc is not None
        document_id = existing_doc['id'] if is_update else None

        # Reindex document (handles deletion of old chunks and indexing new content)
        chunk_count = self._reindex_document(filename, content, is_new=not is_update)

        # Calculate document statistics
        word_count = len(content.split())
        line_count = len(content.splitlines())

        metadata = {
            'word_count': word_count,
            'line_count': line_count,
            'chunk_count': chunk_count
        }

        # Save to database
        try:
            if is_update:
                self.db.update_document(document_id, {
                    'content': content,
                    **metadata
                })
            else:
                document_id = self.db.create_document(filename, content, metadata)
        except Exception as e:
            logger.error(f"Database operation failed for {filename}: {str(e)}")
            # Try to clean up RAG chunks if DB fails
            try:
                self.rag.delete_document(filename)
            except:
                pass
            raise ValidationError(f"Failed to save document: {str(e)}")

        return {
            'message': 'Document updated successfully' if is_update else 'Document uploaded successfully',
            'filename': filename,
            'document_id': document_id,
            'is_update': is_update,
            **metadata
        }

    def create_from_search(self, query: str, filename: str) -> Dict[str, Any]:
        """
        Create a document from web search results using Perplexity API.

        Args:
            query: Search query
            filename: Name for the new document

        Returns:
            Dict with document info

        Raises:
            ValidationError: If search fails or document creation fails
        """
        logger.info(f"Creating document from search: query='{query}', filename={filename}")

        # Check if filename already exists
        existing = self.db.get_document_by_filename(filename)
        if existing:
            raise ValidationError(f"Document '{filename}' already exists")

        # Perform search
        try:
            search_service = self.search_manager.getService("perplexity")
            search_results = search_service.search(query, max_tokens=2000, temperature=0.1)
            logger.info(f"Search returned {len(search_results)} results")
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            raise ValidationError(f"Search failed: {str(e)}")

        # Return error if no search results (e.g., API unauthorized or no content)
        if not search_results:
            raise ValidationError("Search returned no results. This may be due to an invalid Perplexity API key or other search service issues.")

        # Format content for search results
        content_parts = [f"# Search Results for: {query}\n"]
        
        for result in search_results:
            # Handle generated content
            if result.is_generated:
                content_parts.append(f"\n## Generated Answer\n")
                content_parts.append(result.content)
                
                # Add citations if available
                if result.citations:
                    content_parts.append(f"\n### Sources\n")
                    for j, citation in enumerate(result.citations, 1):
                        content_parts.append(f"{j}. {citation}")
            # Handle citation links
            elif result.metadata.get('is_citation'):
                content_parts.append(f"\n### {result.title}\n")
                content_parts.append(f"Source URL: {result.url}\n")
            # Regular search results
            else:
                content_parts.append(f"\n## {result.title}")
                if result.url:
                    content_parts.append(f"URL: {result.url}")
                content_parts.append(f"\n{result.content}\n")
        
        content_parts.append("\n---\n")
        content_parts.append(f"*Document created from web search using {search_service.get_service_name()}*\n")
        content_parts.append(f"*Query: {query}*\n")
        content_parts.append(f"*Generated on: {self._get_current_timestamp()}*")
        
        content = '\n'.join(content_parts)

        # Calculate statistics
        word_count = len(content.split())
        line_count = len(content.splitlines())

        # Index in RAG (this is a new document, so skip deletion of old chunks)
        chunk_count = self._reindex_document(filename, content, is_new=True)

        # Save to database
        metadata = {
            'word_count': word_count,
            'line_count': line_count,
            'chunk_count': chunk_count
        }

        try:
            document_id = self.db.create_document(filename, content, metadata)
            logger.debug(f"Created search document {filename} with ID {document_id}")
        except Exception as e:
            logger.error(f"Failed to save search document: {str(e)}")
            # Clean up RAG chunks
            try:
                self.rag.delete_document(filename)
            except:
                pass
            raise ValidationError(f"Failed to save document: {str(e)}")

        return {
            'message': 'Document created from web search',
            'filename': filename,
            'document_id': document_id,
            'content': content,
            'search_query': query,
            'search_sources': len(search_results),
            **metadata
        }

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents with formatted data (legacy method for backward compatibility)."""
        result = self.db.get_all_documents(page=1, per_page=1000)  # Large page for backward compatibility
        documents = result['documents']

        # Format timestamps
        for doc in documents:
            doc['uploaded_at'] = doc.get('created_at')

        return documents
    
    def get_paginated_documents(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get documents with pagination."""
        result = self.db.get_all_documents(page=page, per_page=per_page)

        # Format timestamps
        for doc in result['documents']:
            doc['uploaded_at'] = doc.get('created_at')

        return result

    def get_document(self, filename: str) -> Dict[str, Any]:
        """
        Get document by filename with content loaded from file storage.

        Args:
            filename: Document filename

        Returns:
            Document data with full content

        Raises:
            NotFoundError: If document doesn't exist
        """
        logger.debug(f"Fetching document: {filename}")
        document = self.db.get_document_by_filename(filename, include_content=True)

        if not document:
            logger.warning(f"Document not found: {filename}")
            raise NotFoundError(f"Document '{filename}' not found")

        return document

    def get_document_with_chat(self, filename: str) -> Dict[str, Any]:
        """
        Get document with chat history, loading content from file storage.

        Args:
            filename: Document filename

        Returns:
            Document data with chat history and full content. chat_history is always a list.

        Raises:
            NotFoundError: If document doesn't exist
        """
        logger.debug(f"Fetching document with chat: {filename}")
        document = self.db.get_document_by_filename(filename, include_content=True)

        if not document:
            logger.warning(f"Document not found: {filename}")
            raise NotFoundError(f"Document '{filename}' not found")

        # Get chat history (always returns a list by default)
        chat_history = self.db.get_chat_history(document['id'])

        return {
            'document': document,
            'chat_history': chat_history
        }

    def update_document(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Update document content.

        Args:
            filename: Document filename
            content: New content

        Returns:
            Success message

        Raises:
            NotFoundError: If document doesn't exist
            ValidationError: If update fails
        """
        logger.debug(f"Updating document: {filename}")
        document = self.db.get_document_by_filename(filename)

        if not document:
            logger.warning(f"Document not found: {filename}")
            raise NotFoundError(f"Document '{filename}' not found")

        document_id = document['id']

        # Reindex document with new content (delete old chunks since this is an update)
        chunk_count = self._reindex_document(filename, content, is_new=False)

        # Update database
        word_count = len(content.split())
        line_count = len(content.splitlines())

        try:
            self.db.update_document(document_id, {
                'content': content,
                'word_count': word_count,
                'line_count': line_count,
                'chunk_count': chunk_count
            })
            logger.debug(f"Updated document {filename} in database")
        except Exception as e:
            logger.error(f"Failed to update document in database: {str(e)}")
            raise ValidationError(f"Failed to update document: {str(e)}")

        return {'message': 'Document updated successfully'}

    def delete_document(self, filename: str) -> Dict[str, Any]:
        """
        Delete a document.

        Args:
            filename: Document filename

        Returns:
            Success message with document info

        Raises:
            NotFoundError: If document doesn't exist
        """
        logger.debug(f"Deleting document: {filename}")
        document = self.db.get_document_by_filename(filename)

        if not document:
            logger.warning(f"Document not found: {filename}")
            raise NotFoundError(f"Document '{filename}' not found")

        document_id = document['id']

        # Delete from RAG
        try:
            self.rag.delete_document(filename)
            logger.debug(f"Deleted RAG chunks for {filename}")
        except Exception as e:
            logger.warning(f"Failed to delete RAG chunks: {str(e)}")

        # Delete from database (cascades to chat history)
        try:
            self.db.delete_document(document_id)
            logger.debug(f"Deleted document {filename} from database")
        except Exception as e:
            logger.error(f"Failed to delete from database: {str(e)}")
            raise ValidationError(f"Failed to delete document: {str(e)}")

        return {
            'message': 'Document deleted successfully',
            'filename': filename,
            'document_id': document_id
        }


# Singleton instance
_document_service = None


def get_document_service() -> DocumentService:
    """Get or create the singleton document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
