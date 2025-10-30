"""File-based storage for document content to reduce database bloat."""

import os
import hashlib
import json
import logging
import shutil
import re
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from app.utils.string_utils import truncate_content

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Manages file-based storage for document content."""

    def __init__(self, storage_path: str = './data/documents'):
        """
        Initialize document storage.

        Args:
            storage_path: Base directory for document storage
        """
        self.storage_path = Path(storage_path)
        self.metadata_path = self.storage_path / 'metadata'
        
        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Document storage initialized at {self.storage_path}")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename
            
        Raises:
            ValueError: If filename is invalid or contains path traversal
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")
        
        # Reject absolute paths and path traversal attempts
        if filename.startswith('/') or '..' in filename:
            raise ValueError(f"Invalid filename: {filename}")
        
        # Remove any path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Allow only safe characters: alphanumeric, underscore, hyphen, dot
        sanitized = re.sub(r'[^\w\-\. ]', '', filename)
        
        if not sanitized:
            raise ValueError(f"Filename contains no valid characters: {filename}")
        
        return sanitized

    def _get_file_path(self, filename: str, create: bool = False) -> Path:
        """
        Get the file path for a document.

        Args:
            filename: Document filename
            create: If True, ensure the directory exists

        Returns:
            Path to the document file
        """
        # Create a subdirectory based on the first two characters of filename hash
        # to avoid having too many files in one directory
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:2]
        sub_dir = self.storage_path / file_hash
        
        if create:
            sub_dir.mkdir(exist_ok=True)
        
        return sub_dir / filename

    def _get_metadata_path(self, filename: str) -> Path:
        """Get the metadata file path for a document."""
        return self.metadata_path / f"{filename}.meta.json"

    def store_document(self, filename: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store document content and metadata to file system.

        Args:
            filename: Document filename
            content: Document content
            metadata: Optional metadata to store

        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize filename for security
            filename = self._sanitize_filename(filename)
            
            # Store the content
            file_path = self._get_file_path(filename, create=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Store metadata (including file size and checksum)
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'stored_at': datetime.now().isoformat(),
                'file_size': len(content.encode('utf-8')),
                'content_hash': hashlib.md5(content.encode()).hexdigest(),
                'file_path': str(file_path.relative_to(self.storage_path))
            })
            
            # Save metadata
            metadata_path = self._get_metadata_path(filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Document stored: {filename} ({metadata['file_size']} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {filename}: {str(e)}")
            return False

    def load_document(self, filename: str, verify_integrity: bool = True) -> Optional[str]:
        """
        Load document content from file system with optional integrity verification.

        Args:
            filename: Document filename
            verify_integrity: Whether to verify content hash

        Returns:
            Document content or None if not found
        """
        try:
            file_path = self._get_file_path(filename)
            
            if not file_path.exists():
                logger.debug(f"Document file not found: {filename}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify integrity if requested and hash is available
            if verify_integrity:
                metadata = self.load_metadata(filename)
                if metadata and 'content_hash' in metadata:
                    expected_hash = metadata['content_hash']
                    actual_hash = hashlib.md5(content.encode()).hexdigest()
                    if expected_hash != actual_hash:
                        logger.error(f"Content hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
                        return None
            
            logger.debug(f"Document loaded: {filename} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load document {filename}: {str(e)}")
            return None

    def load_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load document metadata from file system.

        Args:
            filename: Document filename

        Returns:
            Document metadata or None if not found
        """
        try:
            metadata_path = self._get_metadata_path(filename)
            
            if not metadata_path.exists():
                logger.debug(f"Metadata file not found: {filename}")
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load metadata for {filename}: {str(e)}")
            return None

    def delete_document(self, filename: str) -> bool:
        """
        Delete document content and metadata from file system.

        Args:
            filename: Document filename

        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._get_file_path(filename)
            metadata_path = self._get_metadata_path(filename)
            
            deleted_files = []
            
            # Delete content file
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
                logger.debug(f"Deleted document file: {file_path}")
            
            # Delete metadata file
            if metadata_path.exists():
                metadata_path.unlink()
                deleted_files.append(str(metadata_path))
                logger.debug(f"Deleted metadata file: {metadata_path}")
            
            if deleted_files:
                logger.info(f"Document deleted: {filename} ({len(deleted_files)} files)")
                return True
            else:
                logger.warning(f"No files found to delete for document: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document {filename}: {str(e)}")
            return False

    def update_document(self, filename: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update document content and metadata.

        Args:
            filename: Document filename
            content: New document content
            metadata: Optional metadata updates

        Returns:
            True if successful, False otherwise
        """
        # Load existing metadata
        existing_metadata = self.load_metadata(filename) or {}
        
        # Update with new metadata
        if metadata:
            existing_metadata.update(metadata)
        
        # Store updated document
        return self.store_document(filename, content, existing_metadata)

    def document_exists(self, filename: str) -> bool:
        """
        Check if document exists in storage.

        Args:
            filename: Document filename

        Returns:
            True if exists, False otherwise
        """
        file_path = self._get_file_path(filename)
        return file_path.exists()

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about storage usage.

        Returns:
            Dictionary with storage statistics
        """
        try:
            total_size = 0
            document_count = 0
            
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.meta.json'):
                    total_size += file_path.stat().st_size
                    document_count += 1
            
            return {
                'storage_path': str(self.storage_path),
                'total_documents': document_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'avg_document_size_kb': round((total_size / document_count) / 1024, 2) if document_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {str(e)}")
            return {}

    def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """
        Clean up orphaned files (files without corresponding metadata or vice versa).

        Returns:
            Dictionary with cleanup results
        """
        try:
            cleaned_up = 0
            
            # Check each metadata file and clean up if content file doesn't exist
            for metadata_file in self.metadata_path.glob('*.meta.json'):
                filename = metadata_file.stem  # Remove .meta.json suffix
                content_file = self._get_file_path(filename)
                
                if not content_file.exists():
                    metadata_file.unlink()
                    cleaned_up += 1
                    logger.debug(f"Cleaned up orphaned metadata: {filename}")
            
            logger.info(f"Cleanup completed: {cleaned_up} files cleaned")
            return {'cleaned_up': cleaned_up}
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {str(e)}")
            return {'errors': 1, 'error': str(e)}


# Singleton instance
_document_storage = None

def get_document_storage() -> DocumentStorage:
    """Get or create the singleton document storage instance."""
    global _document_storage
    if _document_storage is None:
        _document_storage = DocumentStorage()
    return _document_storage
