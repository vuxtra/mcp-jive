#!/usr/bin/env python3
"""
Critical MCP Tool Issues Fix Script

This script addresses the most critical issues identified in the detailed audit:
1. Weaviate query API usage corrections
2. UUID validation implementation
3. Reserved property handling
4. Date format standardization
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


class ToolFixApplier:
    """Applies critical fixes to MCP tool implementations."""
    
    def __init__(self):
        self.src_dir = Path(__file__).parent.parent / "src" / "mcp_server" / "tools"
        self.fixes_applied = []
        self.files_modified = set()
        
    def apply_all_fixes(self):
        """Apply all critical fixes."""
        print("🔧 Applying critical MCP tool fixes...")
        print("=" * 50)
        
        # 1. Fix Weaviate query API usage
        self.fix_weaviate_query_api()
        
        # 2. Add UUID validation
        self.add_uuid_validation()
        
        # 3. Fix reserved property issues
        self.fix_reserved_properties()
        
        # 4. Standardize date formatting
        self.fix_date_formatting()
        
        # Print summary
        self.print_summary()
        
    def fix_weaviate_query_api(self):
        """Fix Weaviate query API usage patterns."""
        print("\n1. 🔍 Fixing Weaviate Query API Usage...")
        
        # Common API fixes
        api_fixes = [
            # Filter method corrections
            (r'\.Filter\(', '.with_where('),
            (r'\.where\(', '.with_where('),
            
            # Query collection method corrections
            (r'collection\.query\.get\(', 'collection.query.fetch_objects('),
            
            # Search method corrections
            (r'collection\.query\.hybrid\(', 'collection.query.hybrid('),
        ]
        
        files_to_fix = [
            "search_discovery.py",
            "task_management.py",
            "client_tools.py",
            "storage_sync.py"
        ]
        
        for filename in files_to_fix:
            file_path = self.src_dir / filename
            if file_path.exists():
                self._apply_regex_fixes(file_path, api_fixes, "Weaviate API")
                
    def add_uuid_validation(self):
        """Add UUID validation to tools that need it."""
        print("\n2. 🆔 Adding UUID Validation...")
        
        # Add UUID validation function to database.py
        database_file = self.src_dir.parent / "database.py"
        if database_file.exists():
            content = database_file.read_text()
            
            # Check if UUID validation already exists
            if "def validate_uuid" not in content:
                uuid_validation = '''
import uuid
from typing import Optional

def validate_uuid(uuid_string: str) -> bool:
    """Validate if a string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

def ensure_valid_uuid(uuid_string: str) -> str:
    """Ensure a string is a valid UUID, generate one if not."""
    if validate_uuid(uuid_string):
        return uuid_string
    return str(uuid.uuid4())
'''
                
                # Insert after imports
                import_pattern = r'(from typing import[^\n]*\n)'
                if re.search(import_pattern, content):
                    content = re.sub(import_pattern, r'\1' + uuid_validation, content)
                    database_file.write_text(content)
                    self.fixes_applied.append("Added UUID validation to database.py")
                    self.files_modified.add(str(database_file))
                    
        # Update tools to use UUID validation
        uuid_fixes = [
            # Add UUID validation before database operations
            (r'(def \w+.*task_id.*:.*\n.*""".*\n.*"""\n)', 
             r'\1    if not validate_uuid(task_id):\n        return [TextContent(type="text", text="Error: Invalid UUID format")]\n\n'),
        ]
        
        files_to_fix = ["task_management.py", "client_tools.py"]
        for filename in files_to_fix:
            file_path = self.src_dir / filename
            if file_path.exists():
                self._apply_regex_fixes(file_path, uuid_fixes, "UUID validation")
                
    def fix_reserved_properties(self):
        """Fix reserved property issues in object creation."""
        print("\n3. 🚫 Fixing Reserved Property Issues...")
        
        reserved_fixes = [
            # Remove 'id' from object creation
            (r'"id":\s*[^,}]+,?\s*', ''),
            (r',\s*"id":\s*[^,}]+', ''),
            
            # Use proper Weaviate object creation
            (r'properties\s*=\s*{([^}]*"id"[^}]*)}', 
             lambda m: f'properties={{{m.group(1).replace('"id":', '# "id": # Reserved property -')}}}'),
        ]
        
        files_to_fix = ["task_management.py", "client_tools.py", "workflow_execution.py"]
        for filename in files_to_fix:
            file_path = self.src_dir / filename
            if file_path.exists():
                self._apply_regex_fixes(file_path, reserved_fixes, "Reserved properties")
                
    def fix_date_formatting(self):
        """Standardize date formatting to RFC3339."""
        print("\n4. 📅 Fixing Date Formatting...")
        
        date_fixes = [
            # Fix datetime formatting
            (r'datetime\.now\(\)\.isoformat\(\)', 
             'datetime.now().isoformat() + "Z"'),
            (r'created_at.*datetime\.now\(\)', 
             'created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"'),
        ]
        
        files_to_fix = ["workflow_execution.py", "progress_tracking.py", "validation_tools.py"]
        for filename in files_to_fix:
            file_path = self.src_dir / filename
            if file_path.exists():
                self._apply_regex_fixes(file_path, date_fixes, "Date formatting")
                
    def _apply_regex_fixes(self, file_path: Path, fixes: List[Tuple], fix_type: str):
        """Apply regex-based fixes to a file."""
        try:
            content = file_path.read_text()
            original_content = content
            
            for pattern, replacement in fixes:
                if callable(replacement):
                    content = re.sub(pattern, replacement, content)
                else:
                    content = re.sub(pattern, replacement, content)
                    
            if content != original_content:
                file_path.write_text(content)
                self.fixes_applied.append(f"{fix_type} fixes applied to {file_path.name}")
                self.files_modified.add(str(file_path))
                print(f"   ✅ Applied {fix_type} fixes to {file_path.name}")
            else:
                print(f"   ℹ️  No {fix_type} fixes needed in {file_path.name}")
                
        except Exception as e:
            print(f"   ❌ Error applying {fix_type} fixes to {file_path.name}: {e}")
            
    def print_summary(self):
        """Print summary of applied fixes."""
        print("\n" + "=" * 50)
        print("📋 FIX APPLICATION SUMMARY")
        print("=" * 50)
        
        print(f"\n✅ Total Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
            
        print(f"\n📁 Files Modified: {len(self.files_modified)}")
        for file_path in sorted(self.files_modified):
            print(f"   • {Path(file_path).name}")
            
        print("\n🔄 Next Steps:")
        print("   1. Run detailed audit again to verify fixes")
        print("   2. Test critical tools manually")
        print("   3. Update tool documentation")
        print("   4. Deploy to staging environment")
        
        print("\n⚠️  Note: Some fixes may require manual review and testing.")


def main():
    """Main fix application function."""
    fixer = ToolFixApplier()
    
    try:
        fixer.apply_all_fixes()
        print("\n🎉 Critical fixes application completed!")
        return 0
    except Exception as e:
        print(f"\n💥 Fix application failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())