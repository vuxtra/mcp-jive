#!/usr/bin/env python3
"""
Check work items in the database to understand the mismatch.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

async def check_work_items():
    """Check work items in the database."""
    try:
        print("🔍 Initializing LanceDB manager...")
        db = LanceDBManager(DatabaseConfig())
        await db.initialize()
        
        print("\n📋 Listing all work items...")
        items = await db.list_work_items()
        print(f"Found {len(items)} work items:")
        
        for item in items:
            print(f"- ID: {item['id']}")
            print(f"  Item ID: {item.get('item_id', 'N/A')}")
            print(f"  Title: {item['title']}")
            print(f"  Status: {item['status']}")
            print()
        
        # Check specific work item
        target_id = '9b59d28c-c768-48e6-ae02-5679e1217c55'
        print(f"🔍 Checking for specific work item: {target_id}")
        specific_item = await db.get_work_item(target_id)
        
        if specific_item:
            print("✅ Found the specific work item!")
            print(f"  Title: {specific_item['title']}")
            print(f"  Status: {specific_item['status']}")
        else:
            print("❌ Specific work item not found")
            
        await db.cleanup()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_work_items())