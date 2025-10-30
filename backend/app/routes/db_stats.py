"""Database statistics routes for monitoring."""
from flask import Blueprint, jsonify, request

from app.database import get_db_service
from app.utils.errors import handle_errors

bp = Blueprint('db_stats', __name__, url_prefix='/api/admin/db')


@bp.route('/stats', methods=['GET'])
@handle_errors
def get_database_stats():
    """Get database connection pool statistics."""
    db_service = get_db_service()
    stats = db_service.get_pool_stats()
    
    # Add basic database stats
    try:
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as doc_count FROM document_ingest_data")
            doc_count = cursor.fetchone()['doc_count']
            
            cursor.execute("SELECT COUNT(*) as chat_count FROM document_chat_history")  
            chat_count = cursor.fetchone()['chat_count']
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        stats.update({
            'document_count': doc_count,
            'chat_count': chat_count,
            'tables': tables
        })
    except Exception as e:
        stats['database_error'] = str(e)
    
    return jsonify(stats), 200


@bp.route('/health', methods=['GET'])
@handle_errors
def check_database_health():
    """Check database connectivity and health."""
    db_service = get_db_service()
    health_info = {
        'status': 'healthy',
        'message': 'Database operating normally',
        'pool_status': get_db_service().get_pool_stats()
    }
    
    # Test database connectivity
    try:
        with db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result and result[0] == 1:
                health_info['connectivity'] = 'ok'
            else:
                health_info['connectivity'] = 'failed'
                health_info['status'] = 'degraded'
    except Exception as e:
        health_info['status'] = 'unhealthy'
        health_info['message'] = f'Database connectivity issue: {str(e)}'
        health_info['connectivity'] = 'failed'
    
    return jsonify(health_info), 200
