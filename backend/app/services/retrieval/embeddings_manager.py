"""Embeddings management utilities for RAG system."""
import logging
from typing import List, Dict, Any, Optional

from haystack import Document
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.document_stores.types import DuplicatePolicy

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Manages embeddings operations including CRUD and pagination."""
    
    def __init__(self, document_store: ChromaDocumentStore):
        self.document_store = document_store
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all indexed documents grouped by filename.

        Returns:
            List of documents with metadata
        """
        logger.info("Retrieving all indexed documents")

        try:
            docs = self.document_store.filter_documents()
            # Group by filename
            files = {}
            for doc in docs:
                filename = doc.meta.get('filename', 'unknown')
                if filename not in files:
                    files[filename] = {
                        'filename': filename,
                        'uploaded_at': doc.meta.get('uploaded_at'),
                        'chunk_count': 0
                    }
                files[filename]['chunk_count'] += 1

            logger.info(f"Found {len(files)} unique documents in store")
            return list(files.values())
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            raise
    
    def delete_document(self, filename: str) -> bool:
        """
        Delete all chunks of a document from the vector store.

        Args:
            filename: Name of the document to delete

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """
        logger.info(f"Deleting document from RAG: {filename}")

        try:
            # Try using Haystack filter first
            docs_to_delete = self.document_store.filter_documents(
                filters={"field": "filename", "operator": "==", "value": filename}
            )

            if not docs_to_delete:
                logger.warning(f"No chunks found in RAG for filename: {filename}")
                return False

            # Delete documents by their IDs
            doc_ids = [doc.id for doc in docs_to_delete]
            self.document_store.delete_documents(doc_ids)

            logger.info(f"Deleted {len(doc_ids)} chunks for document: {filename}")
            return True

        except Exception as e:
            logger.warning(f"Haystack filter deletion failed: {str(e)}, trying direct ChromaDB approach")
            
            # Fallback to ChromaDB direct approach
            try:
                if hasattr(self.document_store, '_client') and hasattr(self.document_store, '_collection_name'):
                    collection = self.document_store._client.get_collection(
                        self.document_store._collection_name or "documents"
                    )
                    
                    # Get all documents with this filename
                    results = collection.get(
                        where={"filename": filename},
                        include=['metadatas', 'documents']
                    )
                    
                    if not results['ids']:
                        logger.warning(f"No chunks found in ChromaDB for filename: {filename}")
                        return False
                    
                    # Delete by IDs
                    collection.delete(ids=results['ids'])
                    
                    logger.info(f"Deleted {len(results['ids'])} chunks for document: {filename} (direct ChromaDB)")
                    return True
                else:
                    logger.error("Cannot access ChromaDB client directly")
                    raise e
                    
            except Exception as e2:
                logger.error(f"Both deletion methods failed: {str(e2)}")
                raise e2
    
    def get_embeddings_paginated(self, page: int = 1, per_page: int = 50, document_id: str = None) -> Dict[str, Any]:
        """
        Get embeddings with pagination support at database level.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            document_id: Optional filter by document_id
            
        Returns:
            Dict with embeddings and pagination info
            
        Raises:
            Exception: If query fails
        """
        try:
            # Access the underlying ChromaDB collection for proper pagination
            # We need to access the internal client since Haystack doesn't expose pagination
            if hasattr(self.document_store, '_client') and hasattr(self.document_store, '_collection_name'):
                collection = self.document_store._client.get_collection(
                    self.document_store._collection_name or "documents"
                )
                
                # Build where clause for filtering
                where_clause = None
                if document_id:
                    where_clause = {"document_id": document_id}

                # Get total count
                if where_clause:
                    total = len(collection.get(where=where_clause)['ids'])
                else:
                    total = collection.count()

                # Calculate offset
                offset = (page - 1) * per_page

                # Get paginated data
                results = collection.get(
                    limit=per_page,
                    offset=offset,
                    where=where_clause,
                    include=['metadatas', 'documents']
                )

                embeddings = []
                for i in range(len(results['documents'])):
                    embeddings.append({
                        'id': results['ids'][i] if i < len(results['ids']) else f"embed_{i}",
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i] if i < len(results['metadatas']) else {}
                    })

                return {
                    'embeddings': embeddings,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
            else:
                # Fallback to filter_documents if internals not available
                filters = None
                if document_id:
                    filters = {"field": "document_id", "operator": "==", "value": document_id}

                docs = self.document_store.filter_documents(filters=filters)
                total = len(docs)
                
                # Manual pagination fallback
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                docs_slice = docs[start_idx:end_idx]

                embeddings = [
                    {
                        'id': doc.id,
                        'content': doc.content,
                        'metadata': doc.meta
                    }
                    for doc in docs_slice
                ]

                return {
                    'embeddings': embeddings,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f"Error getting paginated embeddings: {str(e)}", exc_info=True)
            raise
    
    def delete_embedding_by_id(self, embedding_id: str) -> bool:
        """
        Delete a specific embedding by its ID.
        
        Args:
            embedding_id: The ID of the embedding to delete
            
        Returns:
            True if successful
            
        Raises:
            Exception: If deletion fails
        """
        try:
            self.document_store.delete_documents(ids=[embedding_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting embedding {embedding_id}: {str(e)}", exc_info=True)
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the ChromaDB collection.
        
        Returns:
            Dict with collection info
            
        Raises:
            Exception: If query fails
        """
        try:
            count = self.document_store.count_documents()
            collection_name = getattr(self.document_store, '_collection_name', None) or "documents"
            
            return {
                'collection_name': collection_name,
                'total_embeddings': count
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}", exc_info=True)
            raise
    
    def get_documents_with_embeddings_paginated(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get all documents with their embedding information using pagination at database level.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            Dict with documents and pagination info
            
        Raises:
            Exception: If query fails
        """
        try:
            # Access the underlying ChromaDB collection for better performance
            if hasattr(self.document_store, '_client') and hasattr(self.document_store, '_collection_name'):
                collection = self.document_store._client.get_collection(
                    self.document_store._collection_name or "documents"
                )
                
                # Get all embeddings to group by filename (ChromaDB doesn't support grouping)
                results = collection.get(include=['metadatas', 'documents'])
                
                # Group by filename
                files = {}
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if i < len(results['metadatas']) else {}
                    filename = metadata.get('filename', 'unknown')
                    
                    if filename not in files:
                        files[filename] = {
                            'filename': filename,
                            'uploaded_at': metadata.get('uploaded_at'),
                            'chunk_count': 0,
                            'embeddings': []
                        }
                    
                    files[filename]['chunk_count'] += 1
                    files[filename]['embeddings'].append({
                        'id': results['ids'][i] if i < len(results['ids']) else f"embed_{i}",
                        'content': doc,
                        'metadata': metadata
                    })

                # Convert to list and paginate
                all_documents = list(files.values())
                total = len(all_documents)
                
                # Calculate pagination
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                documents_slice = all_documents[start_idx:end_idx]

                return {
                    'documents': documents_slice,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
            else:
                # Fallback method using Haystack filters
                docs = self.document_store.filter_documents()
                
                # Group by filename
                files = {}
                for doc in docs:
                    filename = doc.meta.get('filename', 'unknown')
                    if filename not in files:
                        files[filename] = {
                            'filename': filename,
                            'uploaded_at': doc.meta.get('uploaded_at'),
                            'chunk_count': 0,
                            'embeddings': []
                        }
                    
                    files[filename]['chunk_count'] += 1
                    files[filename]['embeddings'].append({
                        'id': doc.id,
                        'content': doc.content,
                        'metadata': doc.meta
                    })

                # Convert to list and paginate
                all_documents = list(files.values())
                total = len(all_documents)
                
                # Calculate pagination
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                documents_slice = all_documents[start_idx:end_idx]

                return {
                    'documents': documents_slice,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total + per_page - 1) // per_page
                }
                
        except Exception as e:
            logger.error(f"Error retrieving documents with embeddings: {str(e)}", exc_info=True)
            raise
    
    def clear_all_embeddings(self) -> bool:
        """
        Delete all embeddings from ChromaDB.
        
        Returns:
            True if successful
            
        Raises:
            Exception: If deletion fails
        """
        logger.info("Clearing all embeddings from ChromaDB")
        
        try:
            # Get total count before clearing
            count = self.document_store.count_documents()
            logger.info(f"Deleting {count} embeddings from ChromaDB")
            
            # Delete all documents from the collection
            if hasattr(self.document_store, '_client') and hasattr(self.document_store, '_collection_name'):
                # Use ChromaDB directly for better performance
                collection = self.document_store._client.get_collection(
                    self.document_store._collection_name or "documents"
                )
                # Get all document IDs first, then delete them
                all_docs = collection.get()
                if all_docs['ids']:
                    collection.delete(ids=all_docs['ids'])
                logger.info(f"Cleared {len(all_docs['ids'])} embeddings using ChromaDB directly")
            else:
                # Fallback to Haystack method - get all documents and delete them
                docs = self.document_store.filter_documents()
                doc_ids = [doc.id for doc in docs]
                if doc_ids:
                    self.document_store.delete_documents(document_ids=doc_ids)
                logger.info(f"Cleared {len(doc_ids)} embeddings using Haystack method")
            
            return True
        except Exception as e:
            logger.error(f"Error clearing all embeddings: {str(e)}", exc_info=True)
            raise
