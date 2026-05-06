# app/core/logging_config.py
"""
Centralized logging configuration for production.

Features:
- Structured JSON logging for CloudWatch
- Request tracing with correlation IDs
- Contextual logging (user_id, request_id, etc.)
- Proper log levels
- Performance monitoring
- Error tracking with stack traces
"""

import json
import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextlib import contextmanager
from functools import wraps
import uuid


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging in CloudWatch."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with structured fields."""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add thread and process info
        log_data.update({
            "thread_id": record.thread,
            "process_id": record.process,
        })
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add structured extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        return json.dumps(log_data, default=str)


class CloudWatchLogger:
    """
    Production-ready logger with CloudWatch optimization.
    
    Features:
    - Structured JSON output
    - Request correlation
    - Performance metrics
    - Error aggregation
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with JSON formatter and appropriate handlers."""
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create JSON formatter
        formatter = JSONFormatter()
        
        # Console handler for CloudWatch
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Set appropriate level based on environment
        import os
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        if env == "production":
            self.logger.setLevel(logging.INFO)
        elif env == "testing":
            self.logger.setLevel(logging.WARNING)
        else:  # development
            self.logger.setLevel(logging.DEBUG)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, **kwargs):
        """Debug level logging with structured context."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Info level logging with structured context."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging with structured context."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Error level logging with structured context."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical level logging with structured context."""
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message: str, **kwargs):
        """Exception logging with full traceback."""
        self.logger.exception(message, extra=kwargs)


class RequestLogger:
    """
    Request-scoped logger with correlation tracking.
    
    Usage:
        request_logger = RequestLogger.get_instance()
        request_logger.set_request_context(request_id="123", user_id="456")
        request_logger.info("Processing request", action="validate_input")
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._context = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'RequestLogger':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_request_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **additional_context
    ):
        """Set request-scoped context for all subsequent logs."""
        if request_id:
            self._context["request_id"] = request_id
        if user_id:
            self._context["user_id"] = user_id
        self._context.update(additional_context)
    
    def clear_context(self):
        """Clear request context (typically at end of request)."""
        self._context.clear()
    
    def _get_logger(self, name: str) -> CloudWatchLogger:
        """Get logger with current context."""
        return CloudWatchLogger(name)
    
    def debug(self, message: str, **kwargs):
        """Debug logging with request context."""
        logger = self._get_logger("request")
        logger.debug(message, **{**self._context, **kwargs})
    
    def info(self, message: str, **kwargs):
        """Info logging with request context."""
        logger = self._get_logger("request")
        logger.info(message, **{**self._context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Warning logging with request context."""
        logger = self._get_logger("request")
        logger.warning(message, **{**self._context, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Error logging with request context."""
        logger = self._get_logger("request")
        logger.error(message, **{**self._context, **kwargs})
    
    def critical(self, message: str, **kwargs):
        """Critical logging with request context."""
        logger = self._get_logger("request")
        logger.critical(message, **{**self._context, **kwargs})
    
    def exception(self, message: str, **kwargs):
        """Exception logging with request context and traceback."""
        logger = self._get_logger("request")
        logger.exception(message, **{**self._context, **kwargs})


# Performance monitoring decorator
def log_performance(operation_name: str = None):
    """
    Decorator to log function performance metrics.
    
    Usage:
        @log_performance("database_query")
        async def get_user_data(user_id):
            ...
    """
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = CloudWatchLogger("performance")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Operation completed: {name}",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    success=True
                )
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Operation failed: {name}",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = CloudWatchLogger("performance")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Operation completed: {name}",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    success=True
                )
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Operation failed: {name}",
                    operation=name,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    
    return decorator


# Context manager for operation logging
@contextmanager
def log_operation(operation_name: str, **context):
    """
    Context manager for logging operation lifecycle.
    
    Usage:
        with log_operation("signal_generation", user_id="123"):
            # Do work
            pass
    """
    logger = CloudWatchLogger("operation")
    operation_id = str(uuid.uuid4())
    
    logger.info(
        f"Operation started: {operation_name}",
        operation_id=operation_id,
        operation=operation_name,
        status="started",
        **context
    )
    
    start_time = time.time()
    
    try:
        yield operation_id
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Operation completed: {operation_name}",
            operation_id=operation_id,
            operation=operation_name,
            status="completed",
            duration_ms=round(duration_ms, 2),
            **context
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            f"Operation failed: {operation_name}",
            operation_id=operation_id,
            operation=operation_name,
            status="failed",
            duration_ms=round(duration_ms, 2),
            error_type=type(e).__name__,
            error_message=str(e),
            **context
        )
        raise


# Convenience functions for backward compatibility
def get_logger(name: str) -> CloudWatchLogger:
    """Get a structured logger instance."""
    return CloudWatchLogger(name)


def get_request_logger() -> RequestLogger:
    """Get the request-scoped logger instance."""
    return RequestLogger.get_instance()


# Configure root logger
def configure_logging():
    """Configure application-wide logging."""
    # Set up root logger to use our configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    root_logger.handlers.clear()
    
    # Add our JSON formatter to root
    formatter = JSONFormatter()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


# Initialize logging on import
configure_logging()
