#!/usr/bin/env python3
"""Debug script to examine timestamp formats in Weaviate database."""

import asyncio
import logging
from datetime import datetime
from src.mcp_server.config import ServerConfig
from src.mcp_server.database import WeaviateManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_timestamps():
    """Debug timestamp formats for duplicate work items."""
    try:
        # Initialize config and database
        config = ServerConfig()
        manager = WeaviateManager(config)
        await manager.start()
        
        print("\n=== Debugging Timestamp Issue ===")
        
        # Search for all E-commerce Platform Modernization items
        results = await manager.search_work_items(
            query='"E-commerce Platform Modernization"',
            search_type="keyword",
            limit=10
        )
        
        print(f"\nFound {len(results)} items with title 'E-commerce Platform Modernization'")
        
        for i, result in enumerate(results):
            work_item = result.get("work_item", {})
            item_id = work_item.get("id")
            title = work_item.get("title")
            created_at = work_item.get("created_at")
            updated_at = work_item.get("updated_at")
            
            print(f"\n--- Item {i+1} ---")
            print(f"ID: {item_id}")
            print(f"Title: '{title}'")
            print(f"Created At: {created_at} (type: {type(created_at)})")
            print(f"Updated At: {updated_at} (type: {type(updated_at)})")
            
            # Try to parse the timestamps
            if updated_at:
                try:
                    if isinstance(updated_at, str):
                        # Try different parsing methods
                        print(f"  Raw string: '{updated_at}'")
                        
                        # Try ISO format
                        try:
                            parsed_iso = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            print(f"  Parsed ISO: {parsed_iso}")
                        except Exception as e:
                            print(f"  ISO parsing failed: {e}")
                        
                        # Try removing Z and parsing
                        try:
                            clean_str = updated_at.rstrip('Z')
                            parsed_clean = datetime.fromisoformat(clean_str)
                            print(f"  Parsed clean: {parsed_clean}")
                        except Exception as e:
                            print(f"  Clean parsing failed: {e}")
                            
                    elif hasattr(updated_at, 'isoformat'):
                        print(f"  Already datetime: {updated_at}")
                        print(f"  ISO format: {updated_at.isoformat()}")
                    else:
                        print(f"  Unknown type: {type(updated_at)}")
                        
                except Exception as e:
                    print(f"  Error parsing timestamp: {e}")
            
            # Check if titles match exactly
            if title:
                exact_match = title.strip().lower() == "e-commerce platform modernization"
                print(f"  Exact title match: {exact_match}")
                if not exact_match:
                    print(f"  Title comparison: '{title.strip().lower()}' vs 'e-commerce platform modernization'")
        
        # Test the identifier resolver directly
        print("\n=== Testing Identifier Resolver ===")
        from src.mcp_server.utils.identifier_resolver import IdentifierResolver
        resolver = IdentifierResolver(manager)
        
        # Enable debug logging for resolver
        resolver_logger = logging.getLogger('src.mcp_server.utils.identifier_resolver')
        resolver_logger.setLevel(logging.DEBUG)
        
        resolved_id = await resolver.resolve_work_item_id("E-commerce Platform Modernization")
        print(f"Resolver result: {resolved_id}")
        
        # Get resolution info
        resolution_info = await resolver.get_resolution_info("E-commerce Platform Modernization")
        print(f"\nResolution info: {resolution_info}")
        
    except Exception as e:
        logger.error(f"Error in debug script: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'manager' in locals():
            await manager.stop()

if __name__ == "__main__":
    asyncio.run(debug_timestamps())