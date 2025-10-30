"""Simplified logging configuration for the application."""

import logging
import os
import sys

# Define log levels
LOG_LEVELS = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}


def setup_logging(config=None):
    """
    Setup simplified logging configuration.
    
    Args:
        config: Optional configuration dictionary
    """
    if config is None:
        config = {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file_path': os.getenv('LOG_FILE', './logs/app.log')
        }
    
    # Get log level
    log_level = LOG_LEVELS.get(config['level'].upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Simple console handler with basic formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Simple file handler (if path specified)
    if config.get('file_path'):
        # Ensure log directory exists
        log_dir = os.path.dirname(config['file_path'])
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Basic file handler
        file_handler = logging.FileHandler(config['file_path'])
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress verbose third-party logging
    suppress_loggers = [
        'urllib3.connectionpool',
        'chromadb.telemetry.product.posthog',
        'chromadb.config',
        'haystack.core.component.component',
        'haystack.core.pipeline.base',
        'werkzeug'
    ]
    
    for logger_name in suppress_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {config['level']}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
