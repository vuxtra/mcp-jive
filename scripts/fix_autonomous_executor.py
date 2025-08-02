#!/usr/bin/env python3
"""
Fix autonomous_executor.py to properly work with LanceDB.
"""

import os
import re

def fix_autonomous_executor():
    """Fix autonomous_executor.py to work with LanceDB."""
    file_path = "src/mcp_server/services/autonomous_executor.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the _ensure_execution_collection_exists method
    old_method_pattern = r'async def _ensure_execution_collection_exists\(self\) -> None:.*?(?=async def|def |class |$)'
    new_method = '''async def _ensure_execution_collection_exists(self) -> None:
        """Ensure the ExecutionResult table exists in LanceDB."""
        try:
            # LanceDB tables are created automatically when first accessed
            # Just ensure the database connection is working
            await self.lancedb_manager.ensure_tables_exist()
            self.logger.info(f"✅ LanceDB table '{self.execution_collection}' ready")
        except Exception as e:
            self.logger.error(f"Failed to ensure execution table exists: {e}")
            raise

    '''
    
    content = re.sub(old_method_pattern, new_method, content, flags=re.DOTALL)
    
    # Fix other malformed try blocks and Weaviate references
    replacements = [
        # Fix malformed try blocks
        (r'try:\s*if not client\.collections\.exists\([^)]+\):', 'try:\n            # LanceDB operations'),
        (r'try:\s*collection = client\.collections\.get\([^)]+\)', 'try:\n            # Use LanceDB for operations'),
        # Remove client references
        (r'\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', ''),
        # Replace collection operations
        (r'collection = client\.collections\.get\([^)]+\)', 'table = await self.lancedb_manager.get_table("ExecutionResult")'),
        (r'collection\.data\.insert\([^)]+\)', 'await self.lancedb_manager.create_work_item(execution_data)'),
        (r'collection\.query\.fetch_objects\([^)]+\)', 'await self.lancedb_manager.search_work_items("", {}, limit=100)'),
        # Fix logger references
        (r'\blogger\.', 'self.logger.'),
        # Remove Weaviate imports
        (r'from weaviate\.classes\.config import.*?\n', ''),
        (r'from weaviate\.classes\.query import.*?\n', ''),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Main function."""
    print("🔧 Fixing autonomous_executor.py...")
    
    # Change to project root
    os.chdir('/Users/fbrbovic/Dev/mcp-jive')
    
    try:
        fix_autonomous_executor()
        print("\n✅ autonomous_executor.py has been fixed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())