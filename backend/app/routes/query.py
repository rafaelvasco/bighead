"""Query routes for RAG operations."""
from flask import Blueprint, request, jsonify
import logging

from app.services.query_service import get_query_service
from app.utils.errors import handle_errors
from app.utils.validators import validate_request

bp = Blueprint('query', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/query', methods=['POST'])
@handle_errors
@validate_request({
    'question': {'type': str, 'required': True, 'min_length': 1},
    'document_id': {'type': str, 'required': True, 'min_length': 1},
    'top_k': {'type': int, 'required': False, 'min': 1, 'max': 15}
})
def query_documents():
    """Query the document store using RAG and save to chat history."""
    data = request.get_json()
    logger.info(f"Query received: question='{data['question']}', document_id='{data['document_id']}', top_k={data.get('top_k', 5)}")
    
    query_service = get_query_service()
    result = query_service.query_documents(
        question=data['question'],
        document_id=data['document_id'],
        top_k=data.get('top_k', 5)
    )
    
    logger.info(f"Query result: answer='{result.get('answer', '')[:100]}...'")
    return jsonify(result), 200
