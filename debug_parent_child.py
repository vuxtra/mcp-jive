#!/usr/bin/env python3
"""
Debug script to investigate parent-child relationship issues in get_work_item_children.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig

async def debug_parent_child():
    """Debug the parent-child relationship issue."""
    
    # Initialize LanceDB manager
    config = DatabaseConfig()
    manager = LanceDBManager(config)
    await manager.initialize()
    
    print("=== Debugging Parent-Child Relationships ===")
    
    # Get all work items
    all_items = await manager.list_work_items(limit=100)
    print(f"\nTotal work items found: {len(all_items)}")
    
    # Print all items with their parent relationships
    print("\n=== All Work Items ===")
    for item in all_items:
        item_id = item.get('id', 'unknown')
        title = item.get('title', 'unknown')
        parent_id = item.get('parent_id')
        item_type = item.get('item_type', 'unknown')
        print(f"ID: {item_id}")
        print(f"  Title: {title}")
        print(f"  Type: {item_type}")
        print(f"  Parent ID: {parent_id}")
        print()
    
    # Test specific parent-child relationship
    target_parent_id = "0b6cdcfc-3d1e-400d-9e75-dcd254cde8b0"  # Core Platform Infrastructure
    print(f"\n=== Looking for children of {target_parent_id} ===")
    
    children = []
    for item in all_items:
        item_parent_id = item.get('parent_id')
        item_id = item.get('id', 'unknown')
        title = item.get('title', 'unknown')
        
        print(f"Checking: {item_id} ({title})")
        print(f"  Parent ID: '{item_parent_id}' (type: {type(item_parent_id)})")
        print(f"  Target ID: '{target_parent_id}' (type: {type(target_parent_id)})")
        print(f"  Equal? {item_parent_id == target_parent_id}")
        print(f"  Equal (str)? {str(item_parent_id) == str(target_parent_id)}")
        
        if item_parent_id == target_parent_id:
            children.append(item)
            print(f"  ✅ MATCH FOUND!")
        else:
            print(f"  ❌ No match")
        print()
    
    print(f"\n=== Results ===")
    print(f"Found {len(children)} children for parent {target_parent_id}")
    for child in children:
        print(f"  - {child.get('title')} ({child.get('id')})")
    
    # Test the actual get_work_item_children method
    print(f"\n=== Testing get_work_item_children method ===")
    try:
        method_children = await manager.get_work_item_children(target_parent_id)
        print(f"Method returned {len(method_children)} children")
        for child in method_children:
            print(f"  - {child.get('title')} ({child.get('id')})")
    except Exception as e:
        print(f"Error calling get_work_item_children: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_parent_child())