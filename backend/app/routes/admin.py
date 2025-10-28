"""Admin routes for database management."""
from flask import Blueprint, jsonify, request
from app.database import get_db_service
from app.services.retrieval import get_rag_service
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/tables', methods=['GET'])
def get_tables():
    """Get list of all database tables and their info."""
    try:
        db = get_db_service()
        
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Get table names
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = cursor.fetchall()

            table_info = []
            for (table_name,) in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {
                        'name': col[1],
                        'type': col[2],
                        'nullable': not col[3],
                        'primary_key': bool(col[5])
                    }
                    for col in cursor.fetchall()
                ]

                table_info.append({
                    'name': table_name,
                    'row_count': row_count,
                    'columns': columns
                })

            return jsonify({'tables': table_info})
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """Get data from a specific table."""
    try:
        db = get_db_service()
        
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Validate table name exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))

            if not cursor.fetchone():
                return jsonify({'error': 'Table not found'}), 404

            # Get pagination params
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            offset = (page - 1) * per_page

            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()[0]

            # Get data with pagination
            cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (per_page, offset))
            rows = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            # Convert rows to dicts
            data = [dict(zip(column_names, row)) for row in rows]

            return jsonify({
                'table': table_name,
                'columns': column_names,
                'data': data,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/table/<table_name>/row', methods=['PUT'])
def update_table_row(table_name):
    """Update a row in a table."""
    try:
        data = request.get_json()
        primary_key = data.get('primary_key')
        updates = data.get('updates')

        if not primary_key or not updates:
            return jsonify({'error': 'primary_key and updates required'}), 400

        db = get_db_service()
        
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Validate table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))

            if not cursor.fetchone():
                return jsonify({'error': 'Table not found'}), 404

            # Get primary key column name
            cursor.execute(f"PRAGMA table_info({table_name})")
            pk_column = None
            for col in cursor.fetchall():
                if col[5]:  # pk flag
                    pk_column = col[1]
                    break

            if not pk_column:
                return jsonify({'error': 'Table has no primary key'}), 400

            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [primary_key]

            query = f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = ?"
            cursor.execute(query, values)

            return jsonify({
                'message': 'Row updated successfully',
                'rows_affected': cursor.rowcount
            })
    except Exception as e:
        logger.error(f"Error updating row: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/table/<table_name>/row', methods=['DELETE'])
def delete_table_row(table_name):
    """Delete a row from a table."""
    try:
        data = request.get_json()
        primary_key = data.get('primary_key')

        if not primary_key:
            return jsonify({'error': 'primary_key required'}), 400

        db = get_db_service()
        
        with db._get_connection() as conn:
            cursor = conn.cursor()

            # Validate table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))

            if not cursor.fetchone():
                return jsonify({'error': 'Table not found'}), 404

            # Get primary key column name
            cursor.execute(f"PRAGMA table_info({table_name})")
            pk_column = None
            for col in cursor.fetchall():
                if col[5]:  # pk flag
                    pk_column = col[1]
                    break

            if not pk_column:
                return jsonify({'error': 'Table has no primary key'}), 400

            # Delete row
            query = f"DELETE FROM {table_name} WHERE {pk_column} = ?"
            cursor.execute(query, (primary_key,))

            return jsonify({
                'message': 'Row deleted successfully',
                'rows_affected': cursor.rowcount
            })
    except Exception as e:
        logger.error(f"Error deleting row: {e}")
        return jsonify({'error': str(e)}), 500


def _pre_flight_chroma_check(rag_service) -> bool:
    """
    Perform a pre-flight health check on ChromaDB.
    
    Args:
        rag_service: RAGService instance to check
        
    Returns:
        True if healthy, False otherwise
    """
    try:
        # Simple health check - try to get collection info
        info = rag_service.get_collection_info()
        logger.info(f"ChromaDB pre-flight check passed. Document count: {info.get('total_embeddings', 0)}")
        return True
    except Exception as e:
        logger.warning(f"ChromaDB pre-flight check failed: {str(e)}")
        return False


@bp.route('/chroma/collections', methods=['GET'])
def get_chroma_collections():
    """Get ChromaDB collections info."""
    try:
        rag = get_rag_service()
        
        # Pre-flight validation check ChromaDB health
        if not _pre_flight_chroma_check(rag):
            logger.warning("ChromaDB pre-flight check failed, attempting reinitialization")
            rag = get_rag_service()  # This will trigger reinitialization if needed
            
        collection_info = rag.get_collection_info()
        return jsonify(collection_info)
    except Exception as e:
        logger.error(f"Error getting ChromaDB info: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chroma/embeddings', methods=['GET'])
def get_chroma_embeddings():
    """Get ChromaDB embeddings with pagination at database level."""
    try:
        rag = get_rag_service()
        
        # Pre-flight validation check ChromaDB health
        if not _pre_flight_chroma_check(rag):
            logger.warning("ChromaDB pre-flight check failed, attempting reinitialization")
            rag = get_rag_service()  # This will trigger reinitialization if needed
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        document_id = request.args.get('document_id', None)
        
        # Get paginated embeddings using the RAGService method
        result = rag.get_embeddings_paginated(page, per_page, document_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chroma/documents', methods=['GET'])
def get_chroma_documents():
    """Get ChromaDB documents with their embedding information and pagination."""
    try:
        rag = get_rag_service()
        
        # Pre-flight validation check ChromaDB health
        if not _pre_flight_chroma_check(rag):
            logger.warning("ChromaDB pre-flight check failed, attempting reinitialization")
            rag = get_rag_service()  # This will trigger reinitialization if needed
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get documents with embeddings using the RAGService method
        result = rag.get_documents_with_embeddings_paginated(page, per_page)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting documents with embeddings: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chroma/document/<filename>', methods=['DELETE'])
def delete_document_embeddings(filename):
    """Delete all embeddings for a specific document."""
    try:
        rag = get_rag_service()
        db = get_db_service()
        
        # First get the document from database if it exists
        doc = db.get_document_by_filename(filename)
        
        # Delete all embeddings for the document
        success = rag.delete_document(filename)
        
        if success:
            # Also delete from database if document exists
            if doc:
                db.delete_document(doc['id'])
                logger.info(f"Deleted document {filename} from database as well")
            
            return jsonify({'message': f'All embeddings for document {filename} deleted successfully'})
        else:
            # Check if document exists in database but not in embeddings
            if doc:
                # Delete from database anyways
                db.delete_document(doc['id'])
                return jsonify({'message': f'Document {filename} deleted from database (no embeddings found)'})
            else:
                return jsonify({'error': 'No embeddings or document found for this filename'}), 404
    except Exception as e:
        logger.error(f"Error deleting document embeddings: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/sqlite/clear', methods=['POST'])
def clear_sqlite_database():
    """Clear all data from SQLite database."""
    try:
        db = get_db_service()
        
        # Clear all data using the DatabaseService method
        success = db.clear_all_data()
        
        if success:
            return jsonify({'message': 'SQLite database cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear SQLite database'}), 500
    except Exception as e:
        logger.error(f"Error clearing SQLite database: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/chroma/clear', methods=['POST'])
def clear_chroma_database():
    """Clear all embeddings from ChromaDB."""
    try:
        rag = get_rag_service()
        
        # Clear all embeddings using the RAGService method
        success = rag.clear_all_embeddings()
        
        if success:
            return jsonify({'message': 'ChromaDB cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear ChromaDB'}), 500
    except Exception as e:
        logger.error(f"Error clearing ChromaDB: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/clear-all', methods=['POST'])
def clear_all_databases():
    """Clear all data from both SQLite database and ChromaDB."""
    try:
        db = get_db_service()
        rag = get_rag_service()
        
        # Clear SQLite database
        sqlite_success = db.clear_all_data()
        
        # Clear ChromaDB
        chroma_success = rag.clear_all_embeddings()
        
        if sqlite_success and chroma_success:
            return jsonify({'message': 'All databases cleared successfully'})
        else:
            errors = []
            if not sqlite_success:
                errors.append('Failed to clear SQLite database')
            if not chroma_success:
                errors.append('Failed to clear ChromaDB')
            return jsonify({'error': '; '.join(errors)}), 500
    except Exception as e:
        logger.error(f"Error clearing all databases: {e}")
        return jsonify({'error': str(e)}), 500
