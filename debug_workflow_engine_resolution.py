#!/usr/bin/env python3
"""
Debug script to test workflow engine identifier resolution.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.utils.identifier_resolver import IdentifierResolver

async def debug_resolution():
    """Debug identifier resolution for workflow engine."""
    print("=== Workflow Engine Identifier Resolution Debug ===")
    
    # Initialize components
    config = ServerConfig()
    db_config = DatabaseConfig()
    lancedb_manager = LanceDBManager(db_config)
    await lancedb_manager.initialize()
    
    identifier_resolver = IdentifierResolver(lancedb_manager)
    
    print("\n--- Checking work items in database ---")
    
    # List all work items
    try:
        table = lancedb_manager.get_table("WorkItem")
        result = table.search().limit(20).to_pandas()
        print(f"Found {len(result)} work items in database:")
        
        for i, row in result.iterrows():
            print(f"  {i+1}. ID: {row.get('id', 'N/A')}, Title: '{row.get('title', 'N/A')}', Type: {row.get('item_type', 'N/A')}")
    except Exception as e:
        print(f"Error listing work items: {e}")
        return
    
    print("\n--- Testing identifier resolution ---")
    
    # Test cases
    test_identifiers = [
        "epic-001",
        "Customer Portal Epic",
        "customer portal",
        "init-001",
        "Digital Transformation Initiative"
    ]
    
    for identifier in test_identifiers:
        print(f"\nTesting identifier: '{identifier}'")
        
        try:
            # Get resolution info
            resolution_info = await identifier_resolver.get_resolution_info(identifier)
            print(f"  Resolution info: {json.dumps(resolution_info, indent=2, default=str)}")
            
            # Try to resolve
            resolved_id = await identifier_resolver.resolve_work_item_id(identifier)
            if resolved_id:
                print(f"  ✅ Resolved to: {resolved_id}")
            else:
                print(f"  ❌ Failed to resolve")
                
        except Exception as e:
            print(f"  ❌ Error during resolution: {e}")
    
    print("\n--- Testing search functionality ---")
    
    # Test search directly
    try:
        search_results = await lancedb_manager.search_work_items(
            query="epic",
            search_type="keyword",
            limit=5
        )
        print(f"Search results for 'epic': {len(search_results)} items")
        for i, result in enumerate(search_results):
            work_item = result.get("work_item", {})
            print(f"  {i+1}. ID: {work_item.get('id')}, Title: '{work_item.get('title')}'")
    except Exception as e:
        print(f"Error during search: {e}")
    
    await lancedb_manager.cleanup()
    print("\n=== Debug complete ===")

if __name__ == "__main__":
    asyncio.run(debug_resolution())