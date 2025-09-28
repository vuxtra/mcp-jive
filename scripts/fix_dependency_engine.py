#!/usr/bin/env python3
"""
Fix dependency_engine.py to properly work with LanceDB.
"""

import os
import re

def fix_dependency_engine():
    """Fix dependency_engine.py to work with LanceDB."""
    file_path = "src/mcp_server/services/dependency_engine.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix malformed try blocks and remove Weaviate references
    replacements = [
        # Fix malformed try blocks
        (r'try:\s*collection = client\.collections\.get\([^)]+\)', 'try:\n            # Use LanceDB for dependency operations'),
        (r'try:\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', 'try:\n'),
        # Remove client.collections references
        (r'collection = client\.collections\.get\([^)]+\)', '# LanceDB operations'),
        (r'client\.collections\.get\([^)]+\)', 'await self.lancedb_manager.get_table("WorkItemDependency")'),
        # Replace collection.data operations
        (r'collection\.data\.insert\([^)]+\)', 'await self.lancedb_manager.create_work_item(dependency_data)'),
        (r'collection\.data\.delete_by_id\([^)]+\)', 'await self.lancedb_manager.delete_work_item(dependency_id)'),
        # Fix logger references
        (r'\blogger\.', 'self.logger.'),
        # Remove empty client lines
        (r'\s*client = await self\.lancedb_manager\.get_client\(\)\s*\n', ''),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    # Fix specific method issues
    # Fix remove_dependency method
    remove_method_pattern = r'async def remove_dependency\(self, dependency_id: str\) -> bool:.*?(?=async def|def |class |$)'
    new_remove_method = '''async def remove_dependency(self, dependency_id: str) -> bool:
        """Remove a dependency relationship.
        
        Args:
            dependency_id: ID of the dependency to remove
            
        Returns:
            True if removed successfully
        """
        try:
            # Use LanceDB to remove the dependency
            result = await self.lancedb_manager.delete_work_item(dependency_id)
            
            self.logger.info(f"Removed dependency {dependency_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove dependency {dependency_id}: {e}")
            return False

    '''
    
    content = re.sub(remove_method_pattern, new_remove_method, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Main function."""
    print("🔧 Fixing dependency_engine.py...")
    
    # Change to project root
    os.chdir('/Users/fbrbovic/Dev/mcp-jive')
    
    try:
        fix_dependency_engine()
        print("\n✅ dependency_engine.py has been fixed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())