#!/usr/bin/env python3
"""
Fix remaining get_client() calls in the codebase after LanceDB migration.
"""

import os
import re
from pathlib import Path

def update_hierarchy_manager():
    """Update hierarchy_manager.py to remove get_client() calls."""
    file_path = "src/mcp_server/services/hierarchy_manager.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the _ensure_collection_exists method
    old_method = r'async def _ensure_collection_exists\(self\) -> None:.*?(?=async def|class |def |$)'
    new_method = '''async def _ensure_collection_exists(self) -> None:
        """Ensure the WorkItem table exists in LanceDB."""
        try:
            # LanceDB tables are created automatically when first accessed
            # Just ensure the database connection is working
            await self.lancedb_manager.ensure_tables_exist()
            self.logger.info(f"✅ LanceDB table '{self.collection_name}' ready")
        except Exception as e:
            self.logger.error(f"Failed to ensure table exists: {e}")
            raise

    '''
    
    content = re.sub(old_method, new_method, content, flags=re.DOTALL)
    
    # Replace other get_client() calls
    replacements = [
        # Remove client = await self.lancedb_manager.get_client() lines
        (r'\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', ''),
        # Replace client.collections.get() with direct LanceDB operations
        (r'collection = client\.collections\.get\([^)]+\)', 'table = await self.lancedb_manager.get_table(self.collection_name)'),
        (r'client\.collections\.get\([^)]+\)', 'await self.lancedb_manager.get_table(self.collection_name)'),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")

def update_autonomous_executor():
    """Update autonomous_executor.py to remove get_client() calls."""
    file_path = "src/mcp_server/services/autonomous_executor.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace get_client() calls with direct LanceDB operations
    replacements = [
        # Remove client = await self.lancedb_manager.get_client() lines
        (r'\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', ''),
        # Replace client.collections.get() with direct LanceDB operations
        (r'collection = client\.collections\.get\([^)]+\)', 'table = await self.lancedb_manager.get_table("WorkItem")'),
        (r'client\.collections\.get\([^)]+\)', 'await self.lancedb_manager.get_table("WorkItem")'),
        # Replace collection.data.insert with LanceDB operations
        (r'collection\.data\.insert\([^)]+\)', 'await self.lancedb_manager.create_work_item(work_item_data)'),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")

def update_dependency_engine():
    """Update dependency_engine.py to remove remaining Weaviate references."""
    file_path = "src/mcp_server/services/dependency_engine.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace remaining weaviate_manager references
    replacements = [
        (r'self\.weaviate_manager', 'self.lancedb_manager'),
        (r'weaviate_manager', 'lancedb_manager'),
        # Remove client = await self.weaviate_manager.get_client() lines
        (r'\s*client = await self\.weaviate_manager\.get_client\(\)\s*\n', ''),
        (r'\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', ''),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")

def main():
    """Main function to update all files."""
    print("🔧 Fixing remaining get_client() calls...")
    
    # Change to project root
    os.chdir('/Users/fbrbovic/Dev/mcp-jive')
    
    try:
        update_hierarchy_manager()
        update_autonomous_executor()
        update_dependency_engine()
        
        print("\n✅ All get_client() calls have been fixed!")
        print("\n📋 Next steps:")
        print("1. Test the server startup")
        print("2. Verify all functionality works")
        print("3. Run comprehensive tests")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())