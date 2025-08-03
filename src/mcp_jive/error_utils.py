
"""Standardized Error Handling Utilities"""

import logging
import traceback
from typing import Optional, Dict, Any, Union, Callable, List
from functools import wraps
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Base exception for MCP tool errors."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }

class DatabaseError(MCPError):
    """Database-related errors."""
    
    def __init__(self, message: str, operation: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)
        self.operation = operation

class ValidationError(MCPError):
    """Validation-related errors."""
    
    def __init__(self, message: str, field: str = "unknown", value: Any = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value

class ServiceUnavailableError(MCPError):
    """Service unavailability errors."""
    
    def __init__(self, message: str, service: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SERVICE_UNAVAILABLE", details)
        self.service = service

class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    def handle_database_error(operation: str, error: Exception) -> Dict[str, Any]:
        """Handle database-related errors with standardized response.
        
        Args:
            operation: The database operation that failed
            error: The original exception
            
        Returns:
            Standardized error response
        """
        error_msg = f"Database operation '{operation}' failed"
        
        # Extract specific error details
        details = {
            "operation": operation,
            "original_error": str(error),
            "error_type": type(error).__name__
        }
        
        # Check for specific database error patterns
        error_str = str(error).lower()
        if "connection refused" in error_str or "unavailable" in error_str:
            error_msg += ": Database service is currently unavailable"
            details["suggestion"] = "Please check if the database service is running and accessible"
        elif "timeout" in error_str:
            error_msg += ": Database operation timed out"
            details["suggestion"] = "The operation took too long. Try again or check database performance"
        elif "not found" in error_str:
            error_msg += ": Requested resource not found"
            details["suggestion"] = "Verify that the requested resource exists"
        else:
            details["suggestion"] = "Check database configuration and connectivity"
            
        logger.error(f"{error_msg}: {error}", exc_info=True)
        
        db_error = DatabaseError(error_msg, operation, details)
        return db_error.to_dict()
    
    @staticmethod
    def handle_validation_error(field: str, value: Any, expected: str) -> Dict[str, Any]:
        """Handle validation errors with standardized response.
        
        Args:
            field: The field that failed validation
            value: The invalid value
            expected: Description of expected format
            
        Returns:
            Standardized error response
        """
        error_msg = f"Validation failed for field '{field}'"
        
        details = {
            "field": field,
            "provided_value": str(value) if value is not None else "null",
            "expected_format": expected,
            "suggestion": f"Please provide a valid {expected} for field '{field}'"
        }
        
        logger.warning(f"{error_msg}: expected {expected}, got {value}")
        
        validation_error = ValidationError(error_msg, field, value, details)
        return validation_error.to_dict()
    
    @staticmethod
    def handle_service_unavailable(service: str, operation: str) -> Dict[str, Any]:
        """Handle service unavailability with graceful degradation.
        
        Args:
            service: The unavailable service
            operation: The attempted operation
            
        Returns:
            Standardized error response with fallback suggestions
        """
        error_msg = f"Service '{service}' is currently unavailable for operation '{operation}'"
        
        details = {
            "service": service,
            "operation": operation,
            "suggestion": "The service may be starting up or temporarily unavailable. Please try again in a few moments.",
            "fallback_available": False
        }
        
        logger.warning(error_msg)
        
        service_error = ServiceUnavailableError(error_msg, service, details)
        return service_error.to_dict()
    
    @staticmethod
    def create_success_response(data: Any, message: str = "Operation completed successfully") -> Dict[str, Any]:
        """Create standardized success response.
        
        Args:
            data: The response data
            message: Success message
            
        Returns:
            Standardized success response
        """
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_partial_success_response(data: Any, warnings: List[str], message: str = "Operation completed with warnings") -> Dict[str, Any]:
        """Create standardized partial success response.
        
        Args:
            data: The response data
            warnings: List of warning messages
            message: Success message
            
        Returns:
            Standardized partial success response
        """
        return {
            "success": True,
            "partial": True,
            "message": message,
            "data": data,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

def with_error_handling(operation_name: str):
    """Decorator for standardized error handling in tool functions.
    
    Args:
        operation_name: Name of the operation for error reporting
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, dict) and result.get("error"):
                    return result  # Already an error response
                return ErrorHandler.create_success_response(result, f"{operation_name} completed successfully")
            except ValidationError as e:
                return e.to_dict()
            except DatabaseError as e:
                return e.to_dict()
            except ServiceUnavailableError as e:
                return e.to_dict()
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                error = MCPError(
                    f"Unexpected error during {operation_name}",
                    "INTERNAL_ERROR",
                    {
                        "operation": operation_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                return error.to_dict()
        return wrapper
    return decorator

def with_database_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for database operations with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Only retry on connection/availability errors
                    if ("connection" in error_str or "unavailable" in error_str or 
                        "timeout" in error_str) and attempt < max_retries:
                        logger.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        raise e
                        
            raise last_error
        return wrapper
    return decorator
