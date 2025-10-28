"""Summarization routes."""
from flask import Blueprint, request, jsonify
import logging

from app.services.summarizer import get_summarizer_service
from app.utils.errors import handle_errors
from app.utils.validators import validate_request

bp = Blueprint('summarize', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@bp.route('/summarize', methods=['POST'])
@handle_errors
@validate_request({
    'content': {'type': str, 'required': True, 'min_length': 1},
    'document_id': {'type': str, 'required': True, 'min_length': 1}
})
def summarize_document():
    """Generate a summary of document content and save it."""
    data = request.get_json()
    summarizer = get_summarizer_service()
    result = summarizer.summarize(
        content=data['content'],
        document_id=data['document_id']
    )
    return jsonify(result), 200
