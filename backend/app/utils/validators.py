"""Request validation utilities."""
from flask import request
from functools import wraps
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Validation error exception."""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_request(schema: Dict[str, Dict[str, Any]], source='json'):
    """
    Decorator to validate request data against a schema.

    Args:
        schema: Dictionary defining required fields and their types
            Example: {
                'field_name': {
                    'type': str,
                    'required': True,
                    'min_length': 1,
                    'max_length': 100
                }
            }
        source: Where to get data from ('json', 'form', 'args')

    Raises:
        ValidationError: If validation fails
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get data from appropriate source
            if source == 'json':
                data = request.get_json(silent=True) or {}
            elif source == 'form':
                data = request.form.to_dict()
            elif source == 'args':
                data = request.args.to_dict()
            else:
                raise ValueError(f"Invalid source: {source}")

            errors = []

            # Validate each field in schema
            for field_name, rules in schema.items():
                value = data.get(field_name)

                # Check if required
                if rules.get('required', False) and not value:
                    errors.append(f"Field '{field_name}' is required")
                    continue

                # Skip further validation if optional and not provided
                if not value and not rules.get('required', False):
                    continue

                # Type validation
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"Field '{field_name}' must be of type {expected_type.__name__}")
                    continue

                # String validations
                if isinstance(value, str):
                    if 'min_length' in rules and len(value) < rules['min_length']:
                        errors.append(f"Field '{field_name}' must be at least {rules['min_length']} characters")
                    if 'max_length' in rules and len(value) > rules['max_length']:
                        errors.append(f"Field '{field_name}' must be at most {rules['max_length']} characters")

                # Numeric validations
                if isinstance(value, (int, float)):
                    if 'min' in rules and value < rules['min']:
                        errors.append(f"Field '{field_name}' must be at least {rules['min']}")
                    if 'max' in rules and value > rules['max']:
                        errors.append(f"Field '{field_name}' must be at most {rules['max']}")

                # Choices validation
                if 'choices' in rules and value not in rules['choices']:
                    errors.append(f"Field '{field_name}' must be one of: {', '.join(map(str, rules['choices']))}")

            if errors:
                from .errors import ValidationError as ValidError
                raise ValidError("Validation failed", payload={'errors': errors})

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions: Optional[List[str]] = None):
    """
    Decorator to validate file uploads.

    Args:
        allowed_extensions: List of allowed file extensions (e.g., ['txt', 'md'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                from .errors import ValidationError as ValidError
                raise ValidError("No file provided")

            file = request.files['file']
            if file.filename == '':
                from .errors import ValidationError as ValidError
                raise ValidError("No file selected")

            # Check extension
            if allowed_extensions:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext not in allowed_extensions:
                    from .errors import ValidationError as ValidError
                    raise ValidError(
                        f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
                        payload={'allowed_extensions': allowed_extensions}
                    )

            return f(*args, **kwargs)
        return decorated_function
    return decorator
