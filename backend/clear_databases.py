import os
import shutil
from pathlib import Path
import sqlite3
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_sqlite_database():
    """Clear all data from SQLite database using API."""
    db_path = "./data/big-head.db"
    
    if not os.path.exists(db_path):
        logger.info("SQLite database doesn't exist, nothing to clear")
        return
    
    logger.info("Clearing SQLite database...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            logger.info("No tables found in database")
            conn.close()
            return
        
        logger.info(f"Found tables: {[table[0] for table in tables]}")
        
        # Clear all tables in correct order (respect foreign keys)
        table_names = [table[0] for table in tables]
        
        # Delete from tables in reverse dependency order
        for table_name in reversed(table_names):
            try:
                cursor.execute(f'DELETE FROM {table_name}')
                logger.info(f"Cleared table: {table_name}")
            except Exception as e:
                logger.error(f"Failed to clear table {table_name}: {e}")
        
        # Reset auto-increment sequences
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='document_chat_history'")
        
        # Commit changes
        conn.commit()
        logger.info("SQLite database cleared successfully")
        
        # Get final stats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        remaining_tables = cursor.fetchall()
        if remaining_tables:
            for table_name, in remaining_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                logger.info(f"Table {table_name}: {count} records")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to clear SQLite database: {e}")


def clear_chroma_database():
    """Clear ChromaDB using API."""
    chroma_path = os.getenv('CHROMA_DB_PATH', './data/chroma_db')
    
    try:
        import chromadb
        from haystack_integrations.document_stores.chroma import ChromaDocumentStore
        
        logger.info("Clearing ChromaDB...")
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=chroma_path)
        
        # List collections
        collections = client.list_collections()
        collection_names = [collection.name for collection in collections]
        
        if collection_names:
            logger.info(f"Found collections: {collection_names}")
            
            # Delete all collections
            for collection_name in collection_names:
                try:
                    client.delete_collection(name=collection_name)
                    logger.info(f"Deleted collection: {collection_name}")
                except Exception as e:
                    logger.error(f"Failed to delete collection {collection_name}: {e}")
        else:
            logger.info("No collections found in ChromaDB")
        
        # Also clear any remaining files in ChromaDB directory
        if os.path.exists(chroma_path):
            # Remove specific ChromaDB files but keep the directory
            chroma_files = [
                "chroma.sqlite3",
                "indexes"
            ]
            
            for item in chroma_files:
                item_path = os.path.join(chroma_path, item)
                if os.path.exists(item_path):
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                        logger.info(f"Removed ChromaDB item: {item}")
                    except Exception as e:
                        logger.error(f"Failed to remove {item}: {e}")
        
        logger.info("ChromaDB cleared successfully")
        
    except ImportError:
        logger.error("ChromaDB not installed, cannot clear ChromaDB")
    except Exception as e:
        logger.error(f"Failed to clear ChromaDB: {e}")


def clear_document_storage():
    """Clear the file-based document storage."""
    storage_path = Path("./data/documents")
    
    if not storage_path.exists():
        logger.info("Document storage directory doesn't exist, nothing to clear")
        return
    
    logger.info(f"Clearing document storage at: {storage_path}")
    
    try:
        if storage_path.is_dir():
            # Check if it's non-empty
            if any(storage_path.iterdir()):
                logger.info("Document storage directory contains data, removing...")
                shutil.rmtree(storage_path)
                logger.info("Document storage cleared successfully")
            else:
                logger.info("Document storage directory is already empty")
    except Exception as e:
        logger.error(f"Failed to clear document storage: {e}")


def clear_logs():
    """Clear old log files."""
    log_dir = Path("./logs")
    
    if not log_dir.exists():
        logger.info("No logs directory found")
        return
    
    # Remove log files
    log_files = list(log_dir.glob("*.log*"))
    
    if not log_files:
        logger.info("No log files found")
        return
    
    logger.info(f"Clearing {len(log_files)} log files:")
    for log_file in log_files:
        try:
            log_file.unlink()
            logger.info(f"Deleted log: {log_file}")
        except Exception as e:
            logger.error(f"Failed to delete {log_file}: {e}")


def main():
    """Clear all databases and storage."""
    print("=" * 60)
    print("CLEARING DATABASES FOR FRESH START")
    print("=" * 60)
    print("\nThis script will clear:")
    print("1. SQLite database (using API)")
    print("2. ChromaDB vector store (using API)")
    print("3. File-based document storage")
    print("4. Old log files")
    print("\nClearing databases...")
    
    # Clear each database/storage
    clear_sqlite_database()
    clear_chroma_database()
    clear_document_storage()
    clear_logs()
    
    # Recreate empty directories
    Path("./data").mkdir(exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETED")
    print("=" * 60)
    print("\nAll databases have been cleared.")

if __name__ == "__main__":
    main()
