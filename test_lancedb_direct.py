#!/usr/bin/env python3
"""Test LanceDB manager directly to debug work item retrieval."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.lancedb_manager import LanceDBManager
from mcp_jive.config import ServerConfig

async def test_lancedb_direct():
    """Test LanceDB manager directly."""
    try:
        print("🔧 Initializing LanceDB Manager...")
        config = ServerConfig()
        print(f"📁 LanceDB data path: {config.lancedb_data_path}")
        
        lm = LanceDBManager(config)
        await lm.initialize()
        print("✅ LanceDB Manager initialized")
        
        # Test work item retrieval
        work_item_id = '9b59d28c-c768-48e6-ae02-5679e1217c55'
        print(f"🔍 Testing get_work_item with ID: {work_item_id}")
        
        result = await lm.get_work_item(work_item_id)
        print(f"📊 LanceDB result: {result}")
        
        if result:
            print("✅ Work item found in LanceDB!")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Type: {result.get('item_type', 'N/A')}")
        else:
            print("❌ Work item NOT found in LanceDB")
            
        # List all work items to see what's there
        print("\n📋 Listing all work items...")
        all_items = await lm.list_work_items(limit=10)
        print(f"📊 Found {len(all_items)} work items total")
        
        for i, item in enumerate(all_items[:5]):
            print(f"   {i+1}. ID: {item.get('id', 'N/A')[:8]}... Title: {item.get('title', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lancedb_direct())