#!/usr/bin/env python3
"""Check both LanceDB instances to see where work items are stored."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.lancedb_manager import LanceDBManager
from mcp_server.config import ServerConfig

async def check_database(path, name):
    """Check a specific database path."""
    print(f"\n🔍 Checking {name} at {path}")
    
    try:
        # Create a ServerConfig with the specific path
        config = ServerConfig()
        config.lancedb_data_path = path
        
        manager = LanceDBManager(config)
        await manager.initialize()
        
        # List work items
        work_items = await manager.list_work_items()
        print(f"📊 Found {len(work_items)} work items in {name}")
        
        for item in work_items:
            print(f"  - {item.get('id', 'no-id')}: {item.get('title', 'no-title')}")
        
        await manager.cleanup()
        return len(work_items)
        
    except Exception as e:
        print(f"❌ Error checking {name}: {e}")
        return 0

async def main():
    """Check both database instances."""
    print("🔍 Checking both LanceDB instances...")
    
    # Check original lancedb
    count1 = await check_database('./data/lancedb', 'Original LanceDB')
    
    # Check lancedb_jive
    count2 = await check_database('./data/lancedb_jive', 'Jive LanceDB')
    
    print(f"\n📊 Summary:")
    print(f"  Original LanceDB: {count1} work items")
    print(f"  Jive LanceDB: {count2} work items")
    
    if count1 > 0 and count2 == 0:
        print("\n💡 Work items are in the original LanceDB, not Jive LanceDB!")
        print("   The MCP client tools might be using the original database.")
    elif count2 > 0 and count1 == 0:
        print("\n✅ Work items are correctly in Jive LanceDB.")
    elif count1 > 0 and count2 > 0:
        print("\n⚠️  Work items exist in both databases - potential duplication.")
    else:
        print("\n❌ No work items found in either database.")

if __name__ == "__main__":
    asyncio.run(main())