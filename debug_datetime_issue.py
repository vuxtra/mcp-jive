#!/usr/bin/env python3
"""Debug script to isolate the datetime serialization issue."""

import asyncio
import json
from datetime import datetime
from src.mcp_server.database import WeaviateManager
from src.mcp_server.config import ServerConfig

async def debug_datetime_issue():
    """Debug the datetime serialization issue."""
    try:
        # Initialize database connection
        config = ServerConfig()
        weaviate_manager = WeaviateManager(config)
        await weaviate_manager._connect()
        print("Connected to Weaviate successfully!")
        
        # Test basic datetime serialization
        print("Testing basic datetime serialization...")
        test_datetime = datetime.now()
        print(f"Datetime object: {test_datetime}")
        print(f"Datetime type: {type(test_datetime)}")
        print(f"Datetime isoformat: {test_datetime.isoformat()}")
        
        # Test JSON serialization with default=str
        test_data = {"timestamp": test_datetime}
        try:
            json_str = json.dumps(test_data, default=str)
            print(f"JSON with default=str: {json_str}")
        except Exception as e:
            print(f"JSON serialization failed: {e}")
        
        # Test fetching work item data directly
        print("\nTesting work item data fetching...")
        collection = weaviate_manager.get_collection("WorkItem")
        result = collection.query.fetch_objects(limit=5)
        
        print(f"Found {len(result.objects)} work items")
        
        if result.objects:
            for i, obj in enumerate(result.objects):
                print(f"\n--- Work item {i+1} ---")
                print(f"Work item UUID: {obj.uuid}")
                print(f"Properties keys: {list(obj.properties.keys())}")
                
                # Check each property for datetime objects
                for key, value in obj.properties.items():
                    print(f"Property {key}: {type(value)} = {value}")
                    if hasattr(value, 'isoformat'):
                        print(f"  -> Has isoformat: {value.isoformat()}")
                    elif 'datetime' in str(type(value)).lower():
                        print(f"  -> Is datetime-like: {str(value)}")
                    
                    # Test JSON serialization of this property
                    try:
                        json.dumps(value)
                        print(f"  -> JSON serializable: YES")
                    except Exception as e:
                        print(f"  -> JSON serializable: NO - {e}")
                        
                # Test the specific work item we're having trouble with
                if str(obj.uuid) == "079b61d5-bdd8-4341-8537-935eda5931c7":
                    print(f"\n*** FOUND PROBLEMATIC WORK ITEM ***")
                    # Test child lookup
                    children_found = 0
                    for child_obj in result.objects:
                        if child_obj.properties.get("parent_id") == str(obj.uuid):
                            children_found += 1
                            print(f"Child found: {child_obj.uuid} - {child_obj.properties.get('title')}")
                            
                            # Test child properties
                            for child_key, child_value in child_obj.properties.items():
                                try:
                                    json.dumps(child_value)
                                except Exception as child_e:
                                    print(f"  -> Child property {child_key} NOT serializable: {child_e}")
                    print(f"Total children found: {children_found}")
        else:
            print("No work items found in database")
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_datetime_issue())