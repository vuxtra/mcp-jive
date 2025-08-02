#!/usr/bin/env python3
"""Debug script to test identifier resolution."""

import asyncio
import json
from src.mcp_server.database import WeaviateManager
from src.mcp_server.config import ServerConfig
from src.mcp_server.utils.identifier_resolver import IdentifierResolver

async def debug_identifier_resolution():
    """Debug the identifier resolution issue."""
    try:
        # Initialize database connection
        config = ServerConfig()
        weaviate_manager = WeaviateManager(config)
        await weaviate_manager._connect()
        print("Connected to Weaviate successfully!")
        
        # Initialize identifier resolver
        resolver = IdentifierResolver(weaviate_manager)
        
        # Test the exact title that's failing
        test_title = "E-commerce Platform Modernization"
        print(f"\nTesting identifier resolution for: '{test_title}'")
        
        # Test direct search first
        print("\n1. Testing direct search...")
        search_results = await weaviate_manager.search_work_items(
            query=f'"{test_title}"',
            search_type="keyword",
            limit=10
        )
        print(f"Search returned {len(search_results)} results:")
        for i, result in enumerate(search_results):
            work_item = result.get("work_item", {})
            print(f"  Result {i+1}:")
            print(f"    Title: '{work_item.get('title', 'N/A')}'")
            print(f"    ID: {work_item.get('id', 'N/A')}")
            print(f"    Type: {work_item.get('type', 'N/A')}")
            
            # Test exact match logic
            if work_item.get("title", "").strip().lower() == test_title.strip().lower():
                print(f"    *** EXACT MATCH FOUND! ***")
            else:
                print(f"    No exact match: '{work_item.get('title', '')}' != '{test_title}'")
        
        # Test the resolver's exact title method
        print("\n2. Testing resolver's _find_by_exact_title method...")
        exact_result = await resolver._find_by_exact_title(test_title)
        print(f"Exact title result: {exact_result}")
        
        # Test the full resolution process
        print("\n3. Testing full resolution process...")
        resolved_id = await resolver.resolve_work_item_id(test_title)
        print(f"Full resolution result: {resolved_id}")
        
        # Test resolution info
        print("\n4. Testing resolution info...")
        resolution_info = await resolver.get_resolution_info(test_title)
        print(f"Resolution info: {json.dumps(resolution_info, indent=2)}")
        
        # Test with UUID directly
        print("\n5. Testing UUID resolution...")
        test_uuid = "079b61d5-bdd8-4341-8537-935eda5931c7"
        uuid_result = await resolver.resolve_work_item_id(test_uuid)
        print(f"UUID resolution result: {uuid_result}")
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_identifier_resolution())