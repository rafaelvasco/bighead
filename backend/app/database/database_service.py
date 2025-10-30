"""
SQLite database service for document ingest data and chat history.
"""
import sqlite3
import json
import uuid
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager
import os
import logging
import queue
import time

from app.utils.string_utils import truncate_content

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing SQLite database operations with simple connection pooling."""

    def __init__(self, db_path: str = './data/big-head.db'):
        """Initialize database service with simple connection pool."""
        self.db_path = db_path
        self.pool_size = 3  # Simple fixed pool size
        self._connection_pool = queue.Queue(maxsize=self.pool_size)
        self._pool_stats = {
            'created': 0,
            'acquired': 0,
            'returned': 0
        }

        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database schema
        self._init_db()
        self._initialize_connection_pool()
        
        logger.debug(f"Database service initialized with pool_size={self.pool_size}")

    def _initialize_connection_pool(self):
        """Initialize the connection pool with optimized connections."""
        # Create connections for the pool
        for i in range(self.pool_size):
            try:
                conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,  # Allow sharing between threads
                    timeout=10.0,  # Shorter timeout for small deployment
                    isolation_level=None  # Autocommit mode for better performance
                )
                conn.row_factory = sqlite3.Row
                
                # Essential performance optimizations
                cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging for better concurrency
                cursor.execute('PRAGMA synchronous=NORMAL')  # Balance between safety and performance
                cursor.execute('PRAGMA cache_size=5000')  # 5MB cache (reduced)
                cursor.execute('PRAGMA temp_store=MEMORY')  # Store temp tables in memory
                cursor.execute('PRAGMA foreign_keys=ON')
                cursor.execute('PRAGMA optimize')
                
                self._connection_pool.put(conn)
                self._pool_stats['created'] += 1
                
            except Exception as e:
                logger.error(f"Failed to create connection {i+1}/{self.pool_size}: {str(e)}")
                # Continue with other connections
        
        actual_pool_size = self._connection_pool.qsize()
        logger.debug(f"Database connection pool initialized with {actual_pool_size} connections")
    
    def get_pool_stats(self) -> dict:
        """Get connection pool statistics."""
        current_pool_size = self._connection_pool.qsize()
        return {
            'pool_size': self.pool_size,
            'current_pool_size': current_pool_size,
            'connections_in_use': self._pool_stats['created'] - current_pool_size,
            'total_created': self._pool_stats['created'],
            'total_acquired': self._pool_stats['acquired'],
            'total_returned': self._pool_stats['returned']
        }
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections from pool."""
        conn = None
        
        try:
            # Get connection from pool
            conn = self._connection_pool.get(timeout=2.0)
            self._pool_stats['acquired'] += 1
            
            yield conn
            
        except queue.Empty:
            logger.error("Database connection pool exhausted")
            raise Exception("Database connection pool exhausted")
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self._connection_pool.put(conn, timeout=0.5)
                    self._pool_stats['returned'] += 1
                except queue.Full:
                    # Pool is full, close this connection
                    conn.close()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
                    conn.close()
    
    

    def _init_db(self):
        """Create database tables if they don't exist."""
        # Create a direct connection for initialization since pool isn't ready yet
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=10.0,
            isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        
        # Apply optimizations
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA foreign_keys=ON')

        # Document ingest data table - optimized to not store content directly
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_ingest_data (
                    id TEXT PRIMARY KEY,
                    filename TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    content_preview TEXT,  -- First 500 chars for quick preview
                    content TEXT,  -- Keep for backwards compatibility
                    content_hash TEXT,  -- Hash of content for integrity checking
                    file_path TEXT,     -- Reference to file-based storage
                    word_count INTEGER,
                    line_count INTEGER,
                    chunk_count INTEGER,
                    file_size INTEGER,   -- Size of content file in bytes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        # Check if we need to upgrade the schema by adding missing columns
        cursor.execute("PRAGMA table_info(document_ingest_data)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add missing columns if they don't exist
        if 'content_hash' not in columns:
            cursor.execute('ALTER TABLE document_ingest_data ADD COLUMN content_hash TEXT')
            logger.info("Added missing content_hash column to document_ingest_data table")
            
        if 'file_path' not in columns:
            cursor.execute('ALTER TABLE document_ingest_data ADD COLUMN file_path TEXT')
            logger.info("Added missing file_path column to document_ingest_data table")
            
        if 'file_size' not in columns:
            cursor.execute('ALTER TABLE document_ingest_data ADD COLUMN file_size INTEGER')
            logger.info("Added missing file_size column to document_ingest_data table")
            
        if 'content_preview' not in columns:
            cursor.execute('ALTER TABLE document_ingest_data ADD COLUMN content_preview TEXT')
            logger.info("Added missing content_preview column to document_ingest_data table")

        # Document chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    sender TEXT NOT NULL CHECK(sender IN ('human', 'ai')),
                    message TEXT NOT NULL,
                    sources TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES document_ingest_data(id) ON DELETE CASCADE
                )
            ''')

        # Create optimized indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_document_filename
            ON document_ingest_data(filename)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_document_updated_at
            ON document_ingest_data(updated_at DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_document_id
            ON document_chat_history(document_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_created_at
            ON document_chat_history(created_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chat_document_created 
            ON document_chat_history(document_id, created_at)
        ''')

        cursor.execute('''
            ANALYZE
        ''')
        
        logger.info("Database schema initialized with optimized indexes")
        
        conn.close()

    # ==================== Document Operations ====================

    def create_document(self, filename: str, content: str, metadata: Dict[str, Any]) -> str:
        """Create a new document record using file storage and return the document ID."""
        import hashlib
        document_id = str(uuid.uuid4())
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Store content in file storage
        from ..storage import get_document_storage
        storage = get_document_storage()
        
        # Prepare storage metadata
        storage_metadata = {
            'word_count': metadata.get('word_count'),
            'line_count': metadata.get('line_count'),
            'chunk_count': metadata.get('chunk_count'),
            'summary': metadata.get('summary')
        }
        
        # Store document in file system
        if not storage.store_document(filename, content, storage_metadata):
            raise Exception(f"Failed to store document {filename} in file storage")
        
        # Get stored metadata
        stored_metadata = storage.load_metadata(filename)
        if not stored_metadata:
            raise Exception(f"Failed to retrieve stored metadata for {filename}")
        
        # Generate content preview
        content_preview = truncate_content(content, max_length=500)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_ingest_data
                (id, filename, content_hash, file_path, summary, word_count, line_count, 
                 chunk_count, file_size, content_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                filename,
                content_hash,
                stored_metadata['file_path'],
                metadata.get('summary'),
                metadata.get('word_count'),
                metadata.get('line_count'),
                metadata.get('chunk_count'),
                stored_metadata['file_size'],
                content_preview
            ))
            
            logger.debug(f"Created document record: {filename} (ID: {document_id})")
            return document_id

    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing document record by ID with file storage support."""
        import hashlib
        from ..storage import get_document_storage
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current document info
            cursor.execute('SELECT filename, content_hash FROM document_ingest_data WHERE id = ?', (document_id,))
            current = cursor.fetchone()
            if not current:
                return False
                
            current_filename = current['filename']
            new_filename = updates.get('filename', current_filename)
            
            # Update file storage if content is provided
            storage = get_document_storage()
            new_content_hash = None
            file_size = None
            content_preview = None
            
            if 'content' in updates:
                content = updates['content']
                new_content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Update file storage
                if not storage.update_document(new_filename, content, {
                    'word_count': updates.get('word_count'),
                    'line_count': updates.get('line_count'),
                    'chunk_count': updates.get('chunk_count'),
                    'summary': updates.get('summary')
                }):
                    logger.error(f"Failed to update document {new_filename} in file storage")
                    return False
                
                # Get updated metadata
                stored_metadata = storage.load_metadata(new_filename)
                if stored_metadata:
                    file_size = stored_metadata['file_size']
                    content_preview = truncate_content(content, max_length=500)
                
                # If filename changed, clean up old file
                if new_filename != current_filename:
                    storage.delete_document(current_filename)

            # Build dynamic UPDATE query based on provided fields
            fields = []
            values = []

            for key in ['filename', 'summary', 'word_count', 'line_count', 'chunk_count']:
                if key in updates:
                    fields.append(f"{key} = ?")
                    values.append(updates[key])
            
            # Add file-related fields if content was updated
            if new_content_hash is not None:
                fields.append("content_hash = ?")
                values.append(new_content_hash)
                
            if file_size is not None:
                fields.append("file_size = ?")
                values.append(file_size)
                
            if content_preview is not None:
                fields.append("content_preview = ?")
                values.append(content_preview)

            if not fields:
                return False

            # Always update updated_at
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(document_id)

            query = f"UPDATE document_ingest_data SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            
            logger.debug(f"Updated document record: {new_filename} (ID: {document_id})")
            return cursor.rowcount > 0

    def get_document_by_id(self, document_id: str, include_content: bool = False) -> Optional[Dict[str, Any]]:
        """Get document by ID, optionally including full content from file storage."""
        from ..storage import get_document_storage
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM document_ingest_data WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            document = dict(row)
            
            # Load content from file storage if requested
            if include_content:
                storage = get_document_storage()
                content = storage.load_document(document['filename'])
                if content is not None:
                    document['content'] = content
                else:
                    logger.warning(f"Content not found in file storage for: {document['filename']}")
                    document['content'] = ''
            
            return document

    def get_document_by_filename(self, filename: str, include_content: bool = False) -> Optional[Dict[str, Any]]:
        """Get document by filename, optionally including full content from file storage."""
        from ..storage import get_document_storage
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM document_ingest_data WHERE filename = ?', (filename,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            document = dict(row)
            
            # Load content from file storage if requested
            if include_content:
                storage = get_document_storage()
                content = storage.load_document(filename)
                if content is not None:
                    document['content'] = content
                else:
                    logger.warning(f"Content not found in file storage for: {filename}")
                    document['content'] = ''
            
            return document

    def get_all_documents(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get all documents with pagination."""
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 50
            
        offset = (page - 1) * per_page
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute('SELECT COUNT(*) as total FROM document_ingest_data')
            total = cursor.fetchone()['total']
            
            # Get paginated documents
            cursor.execute(
                'SELECT * FROM document_ingest_data ORDER BY updated_at DESC LIMIT ? OFFSET ?',
                (per_page, offset)
            )
            documents = [dict(row) for row in cursor.fetchall()]
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                'documents': documents,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            }

    def delete_document(self, document_id: str) -> bool:
        """Delete document by ID (cascades to chat history) and file storage."""
        from ..storage import get_document_storage
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get filename before deleting from database
            cursor.execute('SELECT filename FROM document_ingest_data WHERE id = ?', (document_id,))
            result = cursor.fetchone()
            
            if result:
                filename = result['filename']
                
                # Delete from file storage
                storage = get_document_storage()
                storage.delete_document(filename)
            
            # Delete from database (cascades to chat history)
            cursor.execute('DELETE FROM document_ingest_data WHERE id = ?', (document_id,))
            
            deleted = cursor.rowcount > 0
            if deleted:
                logger.debug(f"Deleted document and file storage: {filename} (ID: {document_id})")
            
            return deleted

    def rename_document(self, document_id: str, new_filename: str) -> bool:
        """Rename a document."""
        return self.update_document(document_id, {'filename': new_filename})

    # ==================== Chat History Operations ====================

    def add_chat_message(self, document_id: str, sender: str, message: str, sources: Optional[List[Dict]] = None) -> int:
        """Add a chat message to the history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_chat_history (document_id, sender, message, sources)
                VALUES (?, ?, ?, ?)
            ''', (document_id, sender, message, json.dumps(sources) if sources else None))
            return cursor.lastrowid

    def get_chat_history(self, document_id: str, limit: Optional[int] = None, page: int = 1, per_page: int = 50) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Get chat history for a document with optional pagination.
        
        Returns a list by default. Only returns a dict with pagination when explicitly requested via limit/page/per_page.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine if pagination is explicitly requested
            is_paginated_request = limit is None and (page != 1 or per_page != 50)
            
            if limit is not None:
                # Legacy mode: get limited number of messages
                query = '''
                    SELECT * FROM document_chat_history
                    WHERE document_id = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                '''
                cursor.execute(query, (document_id, limit))
            elif is_paginated_request:
                # Paginated mode: return dict with pagination metadata
                # Validate pagination parameters
                if page < 1:
                    page = 1
                if per_page < 1 or per_page > 100:
                    per_page = 50
                    
                offset = (page - 1) * per_page
                
                # Get total count
                cursor.execute(
                    'SELECT COUNT(*) as total FROM document_chat_history WHERE document_id = ?',
                    (document_id,)
                )
                total = cursor.fetchone()['total']
                
                # Get paginated messages
                query = '''
                    SELECT * FROM document_chat_history
                    WHERE document_id = ?
                    ORDER BY created_at ASC
                    LIMIT ? OFFSET ?
                '''
                cursor.execute(query, (document_id, per_page, offset))
                
                # Calculate pagination info
                total_pages = (total + per_page - 1) // per_page
                has_next = page < total_pages
                has_prev = page > 1
                
                pagination_data = {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            else:
                # Default mode: get all messages (no pagination metadata)
                query = '''
                    SELECT * FROM document_chat_history
                    WHERE document_id = ?
                    ORDER BY created_at ASC
                '''
                cursor.execute(query, (document_id,))
            
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg['sources'] = json.loads(msg['sources']) if msg['sources'] else None
                messages.append(msg)
            
            # Return format depends on the type of request
            if is_paginated_request:
                return {
                    'messages': messages,
                    'pagination': pagination_data
                }
            else:
                return messages

    def clear_chat_history(self, document_id: str) -> bool:
        """Clear all chat history for a document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM document_chat_history WHERE document_id = ?', (document_id,))
            return cursor.rowcount > 0

    def clear_all_data(self) -> bool:
        """Clear all data from the database (documents and chat history)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Delete all chat history first
            cursor.execute('DELETE FROM document_chat_history')
            chat_deleted = cursor.rowcount
            
            # Delete all documents
            cursor.execute('DELETE FROM document_ingest_data')
            docs_deleted = cursor.rowcount
            
            # Reset the SQLite sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='document_chat_history'")
            
            logger.info(f"Cleared database: {chat_deleted} chat history entries and {docs_deleted} documents deleted")
            return True

    # ==================== Comprehensive Data Retrieval ====================

    def get_document_with_chat(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document with its complete chat history."""
        document = self.get_document_by_id(document_id)
        if not document:
            return None

        chat_history = self.get_chat_history(document_id)

        return {
            'document': document,
            'chat_history': chat_history
        }

    def get_document_with_chat_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get document with chat history by filename."""
        document = self.get_document_by_filename(filename)
        if not document:
            return None

        return self.get_document_with_chat(document['id'])


# Thread-safe singleton implementation
_db_service = None
_db_service_lock = threading.Lock()

def get_db_service() -> DatabaseService:
    """
    Get or create the singleton database service instance with thread-safe initialization.
    
    Returns:
        DatabaseService instance
    """
    global _db_service
    
    # Double-checked locking pattern for thread safety
    if _db_service is None:
        with _db_service_lock:
            # Check again inside the lock to prevent race conditions
            if _db_service is None:
                logger.info("Initializing new DatabaseService singleton")
                _db_service = DatabaseService()
    else:
        # Log when returning existing instance
        logger.debug("Returning existing DatabaseService instance")
    
    return _db_service
