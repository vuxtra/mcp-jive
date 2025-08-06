
"""UUID Validation and Handling Utilities"""

import uuid
import re
from typing import Optional, Union, List
import logging

logger = logging.getLogger(__name__)

class UUIDValidator:
    """Comprehensive UUID validation and handling utilities."""
    
    # UUID regex pattern for validation
    UUID_PATTERN = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    @staticmethod
    def is_valid_uuid(uuid_string: Union[str, None]) -> bool:
        """Check if a string is a valid UUID.
        
        Args:
            uuid_string: String to validate
            
        Returns:
            True if valid UUID, False otherwise
        """
        if not uuid_string or not isinstance(uuid_string, str):
            return False
            
        try:
            # Try parsing with uuid module
            uuid_obj = uuid.UUID(uuid_string)
            # Also check with regex for format validation
            return bool(UUIDValidator.UUID_PATTERN.match(uuid_string))
        except (ValueError, TypeError, AttributeError):
            return False
    
    @staticmethod
    def validate_uuid(uuid_string: Union[str, None], field_name: str = "id") -> str:
        """Validate UUID and raise descriptive error if invalid.
        
        Args:
            uuid_string: String to validate
            field_name: Name of the field for error messages
            
        Returns:
            Valid UUID string
            
        Raises:
            ValueError: If UUID is invalid
        """
        if not uuid_string:
            raise ValueError(f"{field_name} is required")
            
        if not isinstance(uuid_string, str):
            raise ValueError(f"{field_name} must be a string")
            
        if not UUIDValidator.is_valid_uuid(uuid_string):
            raise ValueError(
                f"{field_name} must be a valid UUID format (e.g., '123e4567-e89b-12d3-a456-426614174000'). "
                f"Received: '{uuid_string}'"
            )
            
        return uuid_string.lower()
    
    @staticmethod
    def ensure_valid_uuid(uuid_string: Union[str, None], generate_if_invalid: bool = True) -> str:
        """Ensure a string is a valid UUID, optionally generate one if invalid.
        
        Args:
            uuid_string: String to validate
            generate_if_invalid: Whether to generate a new UUID if invalid
            
        Returns:
            Valid UUID string
        """
        if UUIDValidator.is_valid_uuid(uuid_string):
            return uuid_string.lower()
            
        if generate_if_invalid:
            new_uuid = str(uuid.uuid4())
            if uuid_string:
                logger.warning(f"Invalid UUID '{uuid_string}' replaced with generated UUID '{new_uuid}'")
            return new_uuid
        else:
            raise ValueError(f"Invalid UUID: {uuid_string}")
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a new UUID v4.
        
        Returns:
            New UUID string
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def validate_uuid_list(uuid_list: List[str], field_name: str = "ids") -> List[str]:
        """Validate a list of UUIDs.
        
        Args:
            uuid_list: List of UUID strings to validate
            field_name: Name of the field for error messages
            
        Returns:
            List of valid UUID strings
            
        Raises:
            ValueError: If any UUID is invalid
        """
        if not isinstance(uuid_list, list):
            raise ValueError(f"{field_name} must be a list")
            
        validated_uuids = []
        for i, uuid_string in enumerate(uuid_list):
            try:
                validated_uuid = UUIDValidator.validate_uuid(uuid_string, f"{field_name}[{i}]")
                validated_uuids.append(validated_uuid)
            except ValueError as e:
                raise ValueError(f"Invalid UUID at index {i}: {e}")
                
        return validated_uuids
    
    @staticmethod
    def extract_uuid_from_path(path: str) -> Optional[str]:
        """Extract UUID from a URL path or string.
        
        Args:
            path: Path string that may contain a UUID
            
        Returns:
            Extracted UUID if found, None otherwise
        """
        matches = UUIDValidator.UUID_PATTERN.findall(path)
        return matches[0] if matches else None
    
    @staticmethod
    def format_uuid_error(uuid_string: str, context: str = "") -> str:
        """Format a descriptive UUID validation error message.
        
        Args:
            uuid_string: The invalid UUID string
            context: Additional context for the error
            
        Returns:
            Formatted error message
        """
        base_msg = f"Invalid UUID format: '{uuid_string}'"
        
        if context:
            base_msg += f" in {context}"
            
        base_msg += ". Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (e.g., '123e4567-e89b-12d3-a456-426614174000')"
        
        # Add specific guidance based on the error
        if not uuid_string:
            base_msg += ". UUID cannot be empty."
        elif len(uuid_string) != 36:
            base_msg += f". UUID must be exactly 36 characters long, got {len(uuid_string)}."
        elif '-' not in uuid_string:
            base_msg += ". UUID must contain hyphens in the correct positions."
        
        return base_msg


# Convenience functions for common operations
def validate_uuid(uuid_string: str, field_name: str = "id") -> str:
    """Convenience function for UUID validation."""
    return UUIDValidator.validate_uuid(uuid_string, field_name)

def is_valid_uuid(uuid_string: str) -> bool:
    """Convenience function for UUID checking."""
    return UUIDValidator.is_valid_uuid(uuid_string)

def generate_uuid() -> str:
    """Convenience function for UUID generation."""
    return UUIDValidator.generate_uuid()

def ensure_valid_uuid(uuid_string: str) -> str:
    """Convenience function for UUID validation with generation fallback."""
    return UUIDValidator.ensure_valid_uuid(uuid_string)

async def validate_work_item_exists(work_item_id: str, storage) -> bool:
    """Validate that a work item exists in storage.
    
    Args:
        work_item_id: UUID of the work item to check
        storage: WorkItemStorage instance
        
    Returns:
        True if work item exists, False otherwise
    """
    try:
        work_item = await storage.get_work_item(work_item_id)
        return work_item is not None
    except Exception as e:
        logger.warning(f"Error checking work item existence for {work_item_id}: {e}")
        return False
