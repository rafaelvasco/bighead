"""Document management routes."""
from flask import Blueprint, request, jsonify
import logging

from app.services.document_service import get_document_service
from app.utils.errors import handle_errors
from app.utils.validators import validate_request, validate_file_upload

bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = logging.getLogger(__name__)


@bp.route('/upload', methods=['POST'])
@handle_errors
@validate_file_upload(allowed_extensions=['txt', 'md'])
def upload_document():
    """Upload and index a document. If document exists, it will be replaced."""
    file = request.files['file']
    doc_service = get_document_service()
    result = doc_service.upload_document(file)
    return jsonify(result), 201 if not result.get('is_update') else 200


@bp.route('/create-from-search', methods=['POST'])
@handle_errors
@validate_request({
    'query': {'type': str, 'required': True, 'min_length': 1},
    'filename': {'type': str, 'required': True, 'min_length': 1}
})
def create_from_search():
    """Create a document from Perplexity API search results."""
    data = request.get_json()
    doc_service = get_document_service()
    result = doc_service.create_from_search(
        query=data['query'],
        filename=data['filename']
    )
    return jsonify(result), 201


@bp.route('/', methods=['GET'])
@handle_errors
def list_documents():
    """List all indexed documents."""
    doc_service = get_document_service()
    documents = doc_service.get_all_documents()
    return jsonify({'documents': documents}), 200


@bp.route('/<filename>', methods=['GET'])
@handle_errors
def get_document(filename):
    """Get document content and metadata."""
    doc_service = get_document_service()
    document = doc_service.get_document(filename)
    return jsonify(document), 200


@bp.route('/<filename>', methods=['PUT'])
@handle_errors
@validate_request({
    'content': {'type': str, 'required': True, 'min_length': 1}
})
def update_document_content(filename):
    """Update document content."""
    data = request.get_json()
    doc_service = get_document_service()
    result = doc_service.update_document(filename, data['content'])
    return jsonify(result), 200


@bp.route('/<filename>', methods=['DELETE'])
@handle_errors
def delete_document(filename):
    """Delete a document and all its chunks from the vector store and database."""
    doc_service = get_document_service()
    result = doc_service.delete_document(filename)
    return jsonify(result), 200


@bp.route('/<filename>/data', methods=['GET'])
@handle_errors
def get_document_data(filename):
    """Get document with its complete data (summary, chat history)."""
    doc_service = get_document_service()
    data = doc_service.get_document_with_chat(filename)
    return jsonify(data), 200
