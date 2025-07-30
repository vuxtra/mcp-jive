#!/usr/bin/env python3
"""
Phase 2: UUID Handling and Validation Fixes

This script implements Phase 2 recommendations from the tool audit:
1. Comprehensive UUID validation
2. Proper ID format handling
3. UUID generation for missing IDs
4. Test data improvements
"""

import os
import re
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any


class UUIDHandlingFixer:
    """Implements Phase 2 UUID handling and validation fixes."""
    
    def __init__(self):
        self.src_dir = Path(__file__).parent.parent / "src" / "mcp_server"
        self.tools_dir = self.src_dir / "tools"
        self.scripts_dir = Path(__file__).parent
        self.fixes_applied = []
        self.files_modified = set()
        
    def apply_all_fixes(self):
        """Apply all Phase 2 UUID fixes."""
        print("🔧 Phase 2: UUID Handling and Validation Fixes")
        print("=" * 60)
        
        # 1. Add comprehensive UUID validation
        self.add_uuid_validation_utilities()
        
        # 2. Update tool implementations with UUID validation
        self.update_tools_with_uuid_validation()
        
        # 3. Fix test data to use valid UUIDs
        self.fix_test_data_uuids()
        
        # 4. Add UUID generation helpers
        self.add_uuid_generation_helpers()
        
        # 5. Update database operations to handle UUIDs properly
        self.update_database_uuid_handling()
        
        # Print summary
        self.print_summary()
        
    def add_uuid_validation_utilities(self):
        """Add comprehensive UUID validation utilities."""
        print("\n1. 🆔 Adding UUID Validation Utilities...")
        
        uuid_utils_content = '''
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
'''
        
        uuid_utils_file = self.src_dir / "uuid_utils.py"
        uuid_utils_file.write_text(uuid_utils_content)
        self.fixes_applied.append("Created comprehensive UUID validation utilities")
        self.files_modified.add(str(uuid_utils_file))
        
    def update_tools_with_uuid_validation(self):
        """Update tool implementations to use UUID validation."""
        print("\n2. 🔧 Updating Tools with UUID Validation...")
        
        # Tools that need UUID validation
        tools_to_update = [
            "task_management.py",
            "client_tools.py",
            "workflow_execution.py",
            "progress_tracking.py"
        ]
        
        for tool_file in tools_to_update:
            file_path = self.tools_dir / tool_file
            if file_path.exists():
                self._add_uuid_validation_to_tool(file_path)
                
    def _add_uuid_validation_to_tool(self, file_path: Path):
        """Add UUID validation to a specific tool file."""
        content = file_path.read_text()
        
        # Add import for UUID utilities
        if "from ..uuid_utils import" not in content:
            import_pattern = r'(from mcp\.types import[^\n]*\n)'
            if re.search(import_pattern, content):
                uuid_import = "from ..uuid_utils import validate_uuid, is_valid_uuid, generate_uuid, UUIDValidator\n"
                content = re.sub(import_pattern, r'\1' + uuid_import, content)
                
        # Add UUID validation to methods that take ID parameters
        uuid_validation_patterns = [
            # Validate task_id parameters
            (r'(async def \w+.*task_id: str.*\n.*"""[^"]*"""\n)', 
             r'\1        # Validate UUID format\n        task_id = validate_uuid(task_id, "task_id")\n\n'),
            
            # Validate work_item_id parameters
            (r'(async def \w+.*work_item_id: str.*\n.*"""[^"]*"""\n)', 
             r'\1        # Validate UUID format\n        work_item_id = validate_uuid(work_item_id, "work_item_id")\n\n'),
            
            # Validate workflow_id parameters
            (r'(async def \w+.*workflow_id: str.*\n.*"""[^"]*"""\n)', 
             r'\1        # Validate UUID format\n        workflow_id = validate_uuid(workflow_id, "workflow_id")\n\n'),
            
            # Validate id parameters in general
            (r'(async def \w+.*\bid: str.*\n.*"""[^"]*"""\n)', 
             r'\1        # Validate UUID format\n        id = validate_uuid(id, "id")\n\n'),
        ]
        
        original_content = content
        for pattern, replacement in uuid_validation_patterns:
            content = re.sub(pattern, replacement, content)
            
        if content != original_content:
            file_path.write_text(content)
            self.fixes_applied.append(f"Added UUID validation to {file_path.name}")
            self.files_modified.add(str(file_path))
            print(f"   ✅ Added UUID validation to {file_path.name}")
        else:
            print(f"   ℹ️  No UUID validation needed in {file_path.name}")
            
    def fix_test_data_uuids(self):
        """Fix test data to use valid UUIDs."""
        print("\n3. 🧪 Fixing Test Data UUIDs...")
        
        # Update audit scripts to use valid UUIDs
        audit_files = [
            "audit_tools.py",
            "detailed_audit_tools.py"
        ]
        
        for audit_file in audit_files:
            file_path = self.scripts_dir / audit_file
            if file_path.exists():
                self._fix_test_uuids_in_file(file_path)
                
    def _fix_test_uuids_in_file(self, file_path: Path):
        """Fix test UUIDs in a specific file."""
        content = file_path.read_text()
        
        # Replace test ID patterns with valid UUIDs
        uuid_fixes = [
            # Replace test-id-123 with valid UUID
            (r'"test-id-123"', f'"{str(uuid.uuid4())}"'),
            (r'"test-value"', '"test-search-term"'),  # Keep non-ID test values as strings
            
            # Generate valid UUIDs for ID fields
            (r'args\[prop_name\] = "test-id-123"', 
             f'args[prop_name] = "{str(uuid.uuid4())}"'),
        ]
        
        original_content = content
        for pattern, replacement in uuid_fixes:
            content = re.sub(pattern, replacement, content)
            
        if content != original_content:
            file_path.write_text(content)
            self.fixes_applied.append(f"Fixed test UUIDs in {file_path.name}")
            self.files_modified.add(str(file_path))
            print(f"   ✅ Fixed test UUIDs in {file_path.name}")
        else:
            print(f"   ℹ️  No test UUID fixes needed in {file_path.name}")
            
    def add_uuid_generation_helpers(self):
        """Add UUID generation helpers to tools."""
        print("\n4. 🔄 Adding UUID Generation Helpers...")
        
        # Update database operations to generate UUIDs when needed
        database_file = self.src_dir / "database.py"
        if database_file.exists():
            content = database_file.read_text()
            
            # Add UUID generation helper
            if "def generate_object_id" not in content:
                uuid_helper = '''
    def generate_object_id(self) -> str:
        """Generate a new UUID for database objects.
        
        Returns:
            New UUID string
        """
        from .uuid_utils import generate_uuid
        return generate_uuid()
        
    def validate_object_id(self, object_id: str, field_name: str = "id") -> str:
        """Validate an object ID.
        
        Args:
            object_id: ID to validate
            field_name: Field name for error messages
            
        Returns:
            Validated ID
            
        Raises:
            ValueError: If ID is invalid
        """
        from .uuid_utils import validate_uuid
        return validate_uuid(object_id, field_name)
'''
                
                # Insert before the last method
                class_end_pattern = r'(\n\s+async def [^\n]+\n[\s\S]*?)$'
                if re.search(class_end_pattern, content):
                    content = re.sub(r'(class [^:]+:[\s\S]*?)(\n\s+async def [^\n]+)', 
                                    r'\1' + uuid_helper + r'\2', content)
                    database_file.write_text(content)
                    self.fixes_applied.append("Added UUID generation helpers to database")
                    self.files_modified.add(str(database_file))
                    
    def update_database_uuid_handling(self):
        """Update database operations to handle UUIDs properly."""
        print("\n5. 🗄️ Updating Database UUID Handling...")
        
        # Update tools to use proper UUID handling in database operations
        tools_to_update = [
            "task_management.py",
            "client_tools.py"
        ]
        
        for tool_file in tools_to_update:
            file_path = self.tools_dir / tool_file
            if file_path.exists():
                self._update_database_operations(file_path)
                
    def _update_database_operations(self, file_path: Path):
        """Update database operations in a tool file."""
        content = file_path.read_text()
        
        # Update database operation patterns
        db_operation_fixes = [
            # Use proper UUID validation before database calls
            (r'(collection\.data\.get_by_id\()([^)]+)(\))', 
             r'\1self.weaviate_manager.validate_object_id(\2)\3'),
            
            # Update object creation to not include reserved 'id' field
            (r'"id":\s*[^,}]+,?\s*', ''),
            
            # Use UUID generation for new objects
            (r'(properties\s*=\s*{[^}]*)(})', 
             r'\1, "uuid": self.weaviate_manager.generate_object_id()\2'),
        ]
        
        original_content = content
        for pattern, replacement in db_operation_fixes:
            content = re.sub(pattern, replacement, content)
            
        if content != original_content:
            file_path.write_text(content)
            self.fixes_applied.append(f"Updated database UUID handling in {file_path.name}")
            self.files_modified.add(str(file_path))
            print(f"   ✅ Updated database UUID handling in {file_path.name}")
        else:
            print(f"   ℹ️  No database UUID updates needed in {file_path.name}")
            
    def print_summary(self):
        """Print summary of applied fixes."""
        print("\n" + "=" * 60)
        print("📋 PHASE 2 UUID FIXES SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ Total Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
            
        print(f"\n📁 Files Modified: {len(self.files_modified)}")
        for file_path in sorted(self.files_modified):
            print(f"   • {Path(file_path).name}")
            
        print("\n🔄 Next Steps:")
        print("   1. Restart the MCP server to load UUID validation")
        print("   2. Run detailed audit with valid test UUIDs")
        print("   3. Verify UUID error reduction")
        print("   4. Proceed to Phase 3: Error handling standardization")
        
        print("\n📊 Expected Improvements:")
        print("   • Elimination of UUID validation errors (4 tools affected)")
        print("   • Proper ID format handling across all tools")
        print("   • Better error messages for invalid UUIDs")
        print("   • Improved tool reliability from ~40-50% to ~60-70%")
        
        print("\n⚠️  Note: Test data now uses valid UUIDs for realistic testing.")


def main():
    """Main fix application function."""
    fixer = UUIDHandlingFixer()
    
    try:
        fixer.apply_all_fixes()
        print("\n🎉 Phase 2 UUID fixes completed successfully!")
        return 0
    except Exception as e:
        print(f"\n💥 Phase 2 fixes failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())