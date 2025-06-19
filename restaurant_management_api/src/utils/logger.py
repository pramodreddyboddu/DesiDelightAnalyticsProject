import logging
import logging.handlers
import os
from datetime import datetime
from flask import request, g, has_request_context

class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request information."""
    
    def format(self, record):
        # Add request information if available
        if has_request_context() and hasattr(g, 'request_id'):
            record.request_id = g.request_id
        else:
            record.request_id = 'N/A'
            
        if has_request_context() and request:
            record.method = request.method
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.method = 'N/A'
            record.url = 'N/A'
            record.remote_addr = 'N/A'
            
        return super().format(record)

def setup_logger(app):
    """Setup comprehensive logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(method)s %(url)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(method)s %(url)s - %(remote_addr)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(method)s %(url)s - %(remote_addr)s - %(message)s\n%(exc_info)s'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return root_logger

def log_request_info():
    """Log request information for debugging."""
    logger = logging.getLogger(__name__)
    logger.info(f"Request started: {request.method} {request.path}")

def log_request_error(error):
    """Log request errors with context."""
    logger = logging.getLogger(__name__)
    logger.error(f"Request error: {str(error)}", exc_info=True)

def log_database_operation(operation, table, record_count=1):
    """Log database operations for monitoring."""
    logger = logging.getLogger('database')
    logger.info(f"DB {operation}: {table} ({record_count} records)")

def log_file_upload(filename, file_type, success, error=None):
    """Log file upload operations."""
    logger = logging.getLogger('file_upload')
    if success:
        logger.info(f"File upload successful: {filename} ({file_type})")
    else:
        logger.error(f"File upload failed: {filename} ({file_type}) - {error}")

def log_user_action(user_id, action, details=None):
    """Log user actions for audit trail."""
    logger = logging.getLogger('user_actions')
    message = f"User {user_id}: {action}"
    if details:
        message += f" - {details}"
    logger.info(message) 