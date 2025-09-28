#!/usr/bin/env python3
"""
Fix hierarchy_manager.py to properly work with LanceDB.
"""

import os
import re

def fix_hierarchy_manager():
    """Fix hierarchy_manager.py to work with LanceDB."""
    file_path = "src/mcp_server/services/hierarchy_manager.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the entire get_children method
    old_method_pattern = r'async def get_children\(self, parent_id: str, include_nested: bool = False\) -> List\[WorkItem\]:.*?(?=async def|class |def |$)'
    
    new_method = '''async def get_children(self, parent_id: str, include_nested: bool = False) -> List[WorkItem]:
        """Get direct children of a work item.
        
        Args:
            parent_id: ID of the parent work item
            include_nested: If True, include all nested children recursively
            
        Returns:
            List of child work items
        """
        try:
            # Query LanceDB for work items with the specified parent_id
            results = await self.lancedb_manager.search_work_items(
                query_text="",
                filters={"parent_id": parent_id},
                limit=1000
            )
            
            children = []
            for result in results:
                # Convert result to WorkItem
                work_item = WorkItem(
                    id=result.get("id", ""),
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    item_type=result.get("item_type", "task"),
                    status=result.get("status", "pending"),
                    priority=result.get("priority", "medium"),
                    parent_id=result.get("parent_id"),
                    project_id=result.get("project_id"),
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                    created_by=result.get("created_by"),
                    assigned_to=result.get("assigned_to"),
                    tags=result.get("tags", []),
                    metadata=result.get("metadata", {})
                )
                children.append(work_item)
            
            if include_nested:
                # Recursively get nested children
                all_children = children.copy()
                for child in children:
                    nested = await self.get_children(child.id, include_nested=True)
                    all_children.extend(nested)
                return all_children
            
            return children
            
        except Exception as e:
            self.logger.error(f"Failed to get children for {parent_id}: {e}")
            raise

    '''
    
    content = re.sub(old_method_pattern, new_method, content, flags=re.DOTALL)
    
    # Fix other method issues
    replacements = [
        # Fix logger reference
        (r'logger\.error', 'self.logger.error'),
        # Remove any remaining Weaviate references
        (r'collection\.query\.fetch_objects', 'table.search().limit'),
        (r'response\.objects', 'results'),
        (r'obj\.properties', 'obj'),
        (r'self\._weaviate_to_work_item\([^)]+\)', 'work_item'),
        # Remove _weaviate_to_work_item method calls
        (r'work_item = self\._weaviate_to_work_item\(obj\)', ''),
    ]
    
    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)
    
    # Remove the _weaviate_to_work_item method entirely if it exists
    weaviate_method_pattern = r'def _weaviate_to_work_item\(self, weaviate_obj\):.*?(?=def |class |async def|$)'
    content = re.sub(weaviate_method_pattern, '', content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def main():
    """Main function."""
    print("🔧 Fixing hierarchy_manager.py...")
    
    # Change to project root
    os.chdir('/Users/fbrbovic/Dev/mcp-jive')
    
    try:
        fix_hierarchy_manager()
        print("\n✅ hierarchy_manager.py has been fixed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())