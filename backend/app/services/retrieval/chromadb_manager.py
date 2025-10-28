"""ChromaDB initialization and recovery management."""
import logging
import os
import time
import shutil
import datetime
from typing import Optional

import chromadb
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from app.config import Config

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages ChromaDB initialization, recovery, and connection validation."""
    
    def __init__(self):
        self.document_store: Optional[ChromaDocumentStore] = None
    
    def initialize_with_retry(self, max_retries: int = 3, initial_delay: float = 1.0) -> ChromaDocumentStore:
        """
        Initialize ChromaDB with exponential backoff retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            
        Returns:
            Initialized ChromaDocumentStore instance
            
        Raises:
            Exception: If initialization fails after all retries
        """
        logger.info(f"Initializing ChromaDB with {max_retries} retries")
        
        for attempt in range(max_retries):
            try:
                # Pre-flight validation - ensure directory exists
                os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
                
                # Try to initialize ChromaDB
                document_store = ChromaDocumentStore(
                    collection_name="documents",
                    persist_path=Config.CHROMA_DB_PATH
                )
                
                # Test the connection by checking count
                count = document_store.count_documents()
                logger.info(f"ChromaDB initialized successfully. Current document count: {count}")
                
                # Clear any stale connections that might exist
                self._validate_chroma_connection(document_store)
                
                self.document_store = document_store
                return document_store
                
            except Exception as e:
                error_msg = str(e)
                is_tenant_error = "Could not connect to tenant" in error_msg
                is_already_exists_error = "already exists" in error_msg
                
                if is_tenant_error or is_already_exists_error:
                    self._log_tenant_operation_error(e, attempt + 1, max_retries)
                    
                    # If it's the last attempt, try more aggressive recovery
                    if attempt == max_retries - 1:
                        logger.info("Attempting aggressive ChromaDB recovery on final attempt")
                        self._aggressive_chroma_recovery()
                    
                    # If not the last attempt, try a gentler approach
                    elif attempt > 0:
                        self._gentle_chroma_cleanup()
                        
                else:
                    logger.error(f"ChromaDB initialization error (attempt {attempt + 1}): {error_msg}")
                
                # If this was the last attempt, raise the exception
                if attempt == max_retries - 1:
                    logger.error(f"ChromaDB initialization failed after {max_retries} attempts")
                    raise
                
                # Calculate backoff delay with exponential increase and jitter
                delay = initial_delay * (2 ** attempt) + (0.1 * time.time() % 1)
                logger.info(f"Retrying ChromaDB initialization in {delay:.2f} seconds...")
                time.sleep(delay)
        
        raise Exception("Failed to initialize ChromaDB after all retries")
    
    def _log_tenant_operation_error(self, error: Exception, attempt: int, max_attempts: int) -> None:
        """
        Log detailed information about tenant-related ChromaDB errors.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
        """
        error_msg = str(error)
        
        # Categorize the tenant error
        if "Could not connect to tenant" in error_msg:
            error_type = "TENANT_CONNECTION"
        elif "already exists" in error_msg:
            error_type = "COLLISION" 
        elif "database" in error_msg.lower():
            error_type = "DATABASE"
        else:
            error_type = "UNKNOWN_TENANT_ISSUE"
        
        # Extract tenant name if present
        tenant_info = "default_tenant"
        if "tenant" in error_msg:
            import re
            tenant_match = re.search(r'tenant[\'"]?\s*[:=]?\s*[\'"]?(\w+)', error_msg)
            if tenant_match:
                tenant_info = tenant_match.group(1)
        
        # Check database state
        db_exists = os.path.exists(Config.CHROMA_DB_PATH)
        db_writable = False
        if db_exists:
            try:
                test_file = os.path.join(Config.CHROMA_DB_PATH, '.test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                db_writable = True
            except:
                pass
        
        # Log detailed error information
        logger.warning(f"ChromaDB {error_type} error on attempt {attempt}/{max_attempts}")
        logger.warning(f"  Tenant: {tenant_info}")
        logger.warning(f"  Database path: {Config.CHROMA_DB_PATH}")
        logger.warning(f"  Database exists: {db_exists}")
        logger.warning(f"  Database writable: {db_writable}")
        logger.warning(f"  Error message: {error_msg}")
        logger.warning(f"  Exception type: {type(error).__name__}")
        
        # Log debugging information for common scenarios
        if error_type == "TENANT_CONNECTION":
            logger.info("  This usually indicates ChromaDB's internal tenant initialization is incomplete")
            logger.info("  Suggestion: Retry logic should resolve this automatically")
        elif error_type == "COLLISION":
            logger.info("  This usually indicates a previous instance left stale state")
            logger.info("  Suggestion: Cleanup of lock files or database recreation may be needed")
    
    def _validate_chroma_connection(self, document_store: ChromaDocumentStore) -> None:
        """
        Validate ChromaDB connection by performing a simple operation.
        
        Args:
            document_store: The ChromaDocumentStore to validate
        """
        try:
            # Simple validation - check if we can access collection info
            if hasattr(document_store, '_client') and hasattr(document_store, '_collection_name'):
                client = document_store._client
                collection_name = document_store._collection_name or "documents"
                
                # Try to get the collection - this validates tenant/connection
                collection = client.get_collection(collection_name)
                count = collection.count()
            else:
                # Fallback validation
                count = document_store.count_documents()
                
        except Exception as e:
            logger.warning(f"ChromaDB connection validation warning: {e}")
            # Don't raise here - just log it as this is just validation
    
    def _gentle_chroma_cleanup(self) -> None:
        """
        Perform gentle cleanup of ChromaDB artifacts without data loss.
        """
        try:
            # Check for lock files that might indicate a previous crash
            lock_files = []
            for root, dirs, files in os.walk(Config.CHROMA_DB_PATH):
                for file in files:
                    if file.endswith('.lock') or file.endswith('.tmp'):
                        lock_files.append(os.path.join(root, file))
            
            if lock_files:
                logger.info(f"Removing {len(lock_files)} stale ChromaDB lock files")
                for lock_file in lock_files:
                    try:
                        os.remove(lock_file)
                    except Exception as e:
                        logger.warning(f"Could not remove lock file {lock_file}: {e}")
                        
        except Exception as e:
            logger.warning(f"Gentle ChromaDB cleanup failed: {e}")
    
    def _aggressive_chroma_recovery(self) -> None:
        """
        Perform aggressive recovery by backing up and recreating the ChromaDB.
        """
        try:
            if os.path.exists(Config.CHROMA_DB_PATH):
                # Create timestamped backup
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{Config.CHROMA_DB_PATH}_backup_{timestamp}"
                
                logger.info(f"Performing aggressive ChromaDB recovery - backing up to {backup_path}")
                shutil.move(Config.CHROMA_DB_PATH, backup_path)
                
                # Ensure the directory exists for fresh initialization
                os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
                
                logger.info(f"ChromaDB database backed up and directory cleared for fresh initialization")
            else:
                logger.info("ChromaDB directory does not exist, will create fresh database")
                os.makedirs(Config.CHROMA_DB_PATH, exist_ok=True)
                
        except Exception as e:
            logger.error(f"Aggressive ChromaDB recovery failed: {e}")
            # Continue anyway - let the main initialization attempt to create the database
