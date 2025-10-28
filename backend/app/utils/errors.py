"""Custom error classes and error handling utilities."""
from flask import jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error."""

    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert error to dictionary for JSON response."""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)


class ValidationError(AppError):
    """Request validation error."""

    def __init__(self, message="Validation failed", payload=None):
        super().__init__(message, status_code=400, payload=payload)


class BadRequestError(AppError):
    """Bad request error."""

    def __init__(self, message="Bad request", payload=None):
        super().__init__(message, status_code=400, payload=payload)


def handle_errors(f):
    """Decorator to handle errors and return consistent JSON responses."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            logger.warning(f"{e.__class__.__name__}: {e.message}")
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'error': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    return decorated_function
