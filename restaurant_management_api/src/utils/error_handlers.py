from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import logging
import traceback
from functools import wraps

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv

class ValidationError(APIError):
    """Raised when validation fails."""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400)
        self.details = details

class AuthenticationError(APIError):
    """Raised when authentication fails."""
    def __init__(self, message="Authentication required"):
        super().__init__(message, status_code=401)

class AuthorizationError(APIError):
    """Raised when authorization fails."""
    def __init__(self, message="Insufficient permissions"):
        super().__init__(message, status_code=403)

class NotFoundError(APIError):
    """Raised when a resource is not found."""
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)

class DatabaseError(APIError):
    """Raised when database operations fail."""
    def __init__(self, message="Database operation failed"):
        super().__init__(message, status_code=500)

def handle_api_error(error):
    """Handle API errors and return JSON response."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def handle_http_error(error):
    """Handle HTTP errors and return JSON response."""
    response = jsonify({
        'error': error.description,
        'status_code': error.code
    })
    response.status_code = error.code
    return response

def handle_validation_error(error):
    """Handle validation errors and return JSON response."""
    response = jsonify({
        'error': 'Validation failed',
        'details': error.messages,
        'status_code': 400
    })
    response.status_code = 400
    return response

def handle_generic_error(error):
    """Handle generic errors and return JSON response."""
    # Log the full error for debugging
    logger.error(f"Unhandled error: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Return a generic error message to the client
    response = jsonify({
        'error': 'Internal server error',
        'status_code': 500
    })
    response.status_code = 500
    return response

def error_handler(f):
    """Decorator to handle errors in route functions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {e.message}")
            return handle_api_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return handle_generic_error(e)
    return decorated_function

def setup_error_handlers(app):
    """Setup error handlers for the Flask application."""
    
    @app.errorhandler(APIError)
    def handle_api_error_handler(error):
        return handle_api_error(error)
    
    @app.errorhandler(HTTPException)
    def handle_http_error_handler(error):
        return handle_http_error(error)
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Endpoint not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            'error': 'Method not allowed',
            'status_code': 405
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        return handle_generic_error(error)

def log_request_error(error, request_info=None):
    """Log request errors with context."""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'request_method': request.method if request else 'N/A',
        'request_url': request.url if request else 'N/A',
        'request_remote_addr': request.remote_addr if request else 'N/A',
        'user_agent': request.headers.get('User-Agent') if request else 'N/A'
    }
    
    if request_info:
        error_info.update(request_info)
    
    logger.error(f"Request error: {error_info}")
    
    if hasattr(error, '__traceback__'):
        logger.error(f"Traceback: {traceback.format_exc()}")

def safe_json_response(data, status_code=200):
    """Safely return JSON response with error handling."""
    try:
        response = jsonify(data)
        response.status_code = status_code
        return response
    except Exception as e:
        logger.error(f"Error creating JSON response: {str(e)}")
        return jsonify({
            'error': 'Error creating response',
            'status_code': 500
        }), 500 