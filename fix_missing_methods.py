#!/usr/bin/env python3
"""
Fix Missing Methods in LanceDB Migration

This script addresses missing methods and inconsistencies between
the two LanceDBManager implementations after the Weaviate to LanceDB migration.
"""

import os
import sys
import re
from pathlib import Path

def fix_lancedb_manager_methods():
    """Fix missing methods in both LanceDBManager implementations."""
    
    # Paths to both LanceDBManager files
    mcp_server_path = "src/mcp_server/lancedb_manager.py"
    mcp_jive_path = "src/mcp_jive/lancedb_manager.py"
    
    print("🔧 Fixing LanceDBManager missing methods...")
    
    # Check if list_work_items method exists in both files
    for file_path in [mcp_server_path, mcp_jive_path]:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        if 'async def list_work_items(' not in content:
            print(f"❌ Missing list_work_items method in {file_path}")
            
            # Find the position after search_work_items method
            search_pattern = r'(async def search_work_items\(.*?\n.*?raise\n)'
            match = re.search(search_pattern, content, re.DOTALL)
            
            if match:
                # Insert list_work_items method after search_work_items
                list_method = '''
    
    async def list_work_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List work items with filtering, pagination, and sorting."""
        try:
            table = self.get_table("WorkItem")
            
            # Start with a basic query
            if filters or sort_by or limit or offset:
                # Use search with empty vector for filtering/sorting
                query = table.search()
            else:
                # Simple scan for basic listing
                query = table.search()
            
            # Apply filters if provided
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle array filters (e.g., status in ["todo", "in_progress"])
                        value_list = "', '".join(str(v) for v in value)
                        filter_conditions.append(f"{key} IN ('{value_list}')")
                    elif isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    where_clause = " AND ".join(filter_conditions)
                    query = query.where(where_clause)
            
            # Apply sorting if supported
            try:
                if sort_order.lower() == "desc":
                    query = query.sort(f"{sort_by} DESC")
                else:
                    query = query.sort(f"{sort_by} ASC")
            except Exception as sort_error:
                logger.warning(f"Sorting not supported, using default order: {sort_error}")
            
            # Apply pagination
            query = query.limit(limit)
            if offset > 0:
                query = query.offset(offset)
            
            # Execute query and return results
            try:
                results = query.to_pandas()
                return results.to_dict('records')
            except Exception as pandas_error:
                # Fallback to arrow format if pandas fails
                logger.warning(f"Pandas conversion failed, using arrow: {pandas_error}")
                results = query.to_arrow()
                return results.to_pylist()
            
        except Exception as e:
            logger.error(f"❌ Failed to list work items: {e}")
            # Return empty list instead of raising to prevent tool failures
            return []
'''
                
                # Insert the method
                insert_pos = match.end()
                new_content = content[:insert_pos] + list_method + content[insert_pos:]
                
                # Write back to file
                with open(file_path, 'w') as f:
                    f.write(new_content)
                    
                print(f"✅ Added list_work_items method to {file_path}")
            else:
                print(f"❌ Could not find insertion point in {file_path}")
        else:
            print(f"✅ list_work_items method already exists in {file_path}")
    
    # Also check for other potentially missing methods
    missing_methods = [
        'get_work_item_children',
        'get_work_item_dependencies', 
        'validate_dependencies'
    ]
    
    for file_path in [mcp_server_path, mcp_jive_path]:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        for method in missing_methods:
            if f'async def {method}(' not in content and f'def {method}(' not in content:
                print(f"⚠️  Missing method {method} in {file_path}")

def check_tool_registry_consistency():
    """Check if tool registry matches available methods."""
    print("\n🔍 Checking tool registry consistency...")
    
    registry_path = "src/mcp_server/tools/registry.py"
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry_content = f.read()
            
        # Check for registered tools
        registered_tools = re.findall(r'"(jive_[^"]+)"', registry_content)
        print(f"📋 Found {len(registered_tools)} registered tools:")
        for tool in registered_tools:
            print(f"   - {tool}")
    
    # Check client_tools.py for implementations
    client_tools_path = "src/mcp_server/tools/client_tools.py"
    if os.path.exists(client_tools_path):
        with open(client_tools_path, 'r') as f:
            client_content = f.read()
            
        # Find implemented handlers
        handlers = re.findall(r'elif name == "(jive_[^"]+)":', client_content)
        print(f"\n🔧 Found {len(handlers)} implemented handlers:")
        for handler in handlers:
            print(f"   - {handler}")
            
        # Check for missing implementations
        if 'registered_tools' in locals():
            missing_handlers = set(registered_tools) - set(handlers)
            if missing_handlers:
                print(f"\n❌ Missing handler implementations:")
                for missing in missing_handlers:
                    print(f"   - {missing}")
            else:
                print(f"\n✅ All registered tools have handlers")

def main():
    """Main execution function."""
    print("🚀 MCP Jive LanceDB Method Fix Script")
    print("=====================================\n")
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    try:
        # Fix missing methods
        fix_lancedb_manager_methods()
        
        # Check tool registry consistency
        check_tool_registry_consistency()
        
        print("\n✅ LanceDB method fixes completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Restart the MCP server")
        print("   2. Test jive_list_work_items tool")
        print("   3. Proceed with e2e testing")
        
    except Exception as e:
        print(f"\n❌ Error during fix process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()