"""
SQLite database service for document ingest data and chat history.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing SQLite database operations."""

    def __init__(self, db_path: str = './data/big-head.db'):
        """Initialize database service and create tables if they don't exist."""
        self.db_path = db_path

        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database schema
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Enable foreign key constraints
        conn.execute('PRAGMA foreign_keys = ON')
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Document ingest data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_ingest_data (
                    id TEXT PRIMARY KEY,
                    filename TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    content TEXT,
                    word_count INTEGER,
                    line_count INTEGER,
                    chunk_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

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

            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_document_filename
                ON document_ingest_data(filename)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_document_id
                ON document_chat_history(document_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_created_at
                ON document_chat_history(created_at)
            ''')

    # ==================== Document Operations ====================

    def create_document(self, filename: str, content: str, metadata: Dict[str, Any]) -> str:
        """Create a new document record and return the document ID."""
        document_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO document_ingest_data
                (id, filename, content, summary, word_count, line_count, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                filename,
                content,
                metadata.get('summary'),
                metadata.get('word_count'),
                metadata.get('line_count'),
                metadata.get('chunk_count')
            ))
            return document_id

    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing document record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic UPDATE query based on provided fields
            fields = []
            values = []

            for key in ['filename', 'content', 'summary', 'word_count', 'line_count', 'chunk_count']:
                if key in updates:
                    fields.append(f"{key} = ?")
                    values.append(updates[key])

            if not fields:
                return False

            # Always update updated_at
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(document_id)

            query = f"UPDATE document_ingest_data SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            return cursor.rowcount > 0

    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM document_ingest_data WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_document_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get document by filename."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM document_ingest_data WHERE filename = ?', (filename,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM document_ingest_data ORDER BY updated_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, document_id: str) -> bool:
        """Delete document by ID (cascades to chat history)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM document_ingest_data WHERE id = ?', (document_id,))
            return cursor.rowcount > 0

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

    def get_chat_history(self, document_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get chat history for a document."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT * FROM document_chat_history
                WHERE document_id = ?
                ORDER BY created_at ASC
            '''
            if limit:
                query += f' LIMIT {limit}'

            cursor.execute(query, (document_id,))
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                msg['sources'] = json.loads(msg['sources']) if msg['sources'] else None
                messages.append(msg)
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


# Singleton instance
_db_service = None

def get_db_service() -> DatabaseService:
    """Get or create the singleton database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
