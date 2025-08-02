#!/usr/bin/env python3
"""Check if there's data in the database."""

import asyncio
from src.mcp_server.database import WeaviateManager
from src.mcp_server.config import ServerConfig

async def check_database():
    """Check database contents."""
    try:
        config = ServerConfig()
        wm = WeaviateManager(config)
        await wm.start()  # Use start() instead of _connect() to handle embedded mode
        print("Connected to Weaviate successfully!")
        
        collection = wm.get_collection('WorkItem')
        result = collection.query.fetch_objects(limit=10)
        
        print(f"Found {len(result.objects)} work items:")
        for obj in result.objects:
            print(f"- {obj.uuid}: {obj.properties.get('title')}")
            
        # Test specific UUID
        test_uuid = "079b61d5-bdd8-4341-8537-935eda5931c7"
        try:
            specific_result = collection.query.fetch_object_by_id(test_uuid)
            if specific_result:
                print(f"\nFound specific UUID {test_uuid}: {specific_result.properties.get('title')}")
            else:
                print(f"\nSpecific UUID {test_uuid} not found")
        except Exception as e:
            print(f"\nError fetching specific UUID: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database())