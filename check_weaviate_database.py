#!/usr/bin/env python3
"""
Check if the old Weaviate database still contains work items.

This script will help us understand if the MCP client tools are still
accessing the old Weaviate database instead of the new LanceDB.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp_jive.database import WeaviateManager
    from mcp_jive.config import Config
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def check_weaviate_database():
    """Check if the old Weaviate database contains work items."""
    print("🔍 Checking old Weaviate database for work items...")
    
    try:
        # Initialize Weaviate manager with old config
        config = Config()
        weaviate_manager = WeaviateManager(config.database)
        
        print(f"📍 Weaviate config: {config.database}")
        print(f"📍 Use embedded: {getattr(config.database, 'use_embedded', 'Unknown')}")
        print(f"📍 Persistence path: {getattr(config.database, 'weaviate_persistence_path', 'Unknown')}")
        
        # Initialize the database
        await weaviate_manager.initialize()
        print("✅ Weaviate database initialized")
        
        # Check if work items exist
        work_items = await weaviate_manager.list_work_items(limit=10)
        print(f"📊 Found {len(work_items)} work items in Weaviate database")
        
        if work_items:
            print("\n📋 Work items found:")
            for i, item in enumerate(work_items[:5], 1):
                print(f"  {i}. ID: {item.get('id', 'Unknown')}, Title: '{item.get('title', 'Unknown')}'")
            
            if len(work_items) > 5:
                print(f"  ... and {len(work_items) - 5} more")
        else:
            print("❌ No work items found in Weaviate database")
        
        # Clean up
        await weaviate_manager.shutdown()
        print("✅ Weaviate database connection closed")
        
        return len(work_items)
        
    except Exception as e:
        print(f"❌ Error checking Weaviate database: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result = asyncio.run(check_weaviate_database())
    print(f"\n🎯 Summary: Found {result} work items in old Weaviate database")
    
    if result > 0:
        print("\n💡 This explains why client tools can see work items but workflow engine cannot!")
        print("   The client tools are still using the old Weaviate database.")
        print("   We need to migrate the data or update the client tools to use LanceDB.")
    else:
        print("\n🤔 No work items found in Weaviate. The issue might be elsewhere.")