#!/usr/bin/env python3
"""Debug script to test identifier resolver in MCP server context."""

import asyncio
import logging
from src.mcp_server.config import ServerConfig
from src.mcp_server.database import WeaviateManager
from src.mcp_server.utils.identifier_resolver import IdentifierResolver
from src.mcp_server.tools.client_tools import MCPClientTools

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Enable debug logging for specific modules
logging.getLogger('src.mcp_server.utils.identifier_resolver').setLevel(logging.DEBUG)
logging.getLogger('src.mcp_server.database').setLevel(logging.DEBUG)
logging.getLogger('src.mcp_server.tools.client_tools').setLevel(logging.DEBUG)

async def debug_mcp_server_context():
    """Debug identifier resolution in exact MCP server context."""
    try:
        print("\n=== Testing MCP Server Context ===")
        
        # Use exact same configuration as MCP server
        config = ServerConfig()
        print(f"Config - Weaviate URL: {config.weaviate_url}")
        print(f"Config - Weaviate Host: {config.weaviate_host}")
        print(f"Config - Weaviate Port: {config.weaviate_port}")
        print(f"Config - Weaviate Embedded: {config.weaviate_embedded}")
        
        # Initialize WeaviateManager exactly like MCP server
        weaviate_manager = WeaviateManager(config)
        await weaviate_manager.start()
        
        # Check health
        health = await weaviate_manager.health_check()
        print(f"\nWeaviate Health: {health}")
        
        # Initialize MCPClientTools exactly like MCP server
        mcp_tools = MCPClientTools(config, weaviate_manager)
        await mcp_tools.initialize()
        
        print("\n=== Testing Direct Resolver ===")
        # Test the resolver directly
        resolver = mcp_tools.identifier_resolver
        
        print("\nTesting resolution with debug logging...")
        resolved_id = await resolver.resolve_work_item_id("E-commerce Platform Modernization")
        print(f"Direct resolver result: {resolved_id}")
        
        # Get resolution info
        resolution_info = await resolver.get_resolution_info("E-commerce Platform Modernization")
        print(f"\nResolution info: {resolution_info}")
        
        print("\n=== Testing MCP Tool Call ===")
        # Test the actual MCP tool call
        arguments = {"work_item_id": "E-commerce Platform Modernization"}
        result = await mcp_tools._get_work_item(arguments)
        print(f"\nMCP tool result: {result}")
        
        print("\n=== Testing Search Directly ===")
        # Test search directly
        search_results = await weaviate_manager.search_work_items(
            query='"E-commerce Platform Modernization"',
            search_type="keyword",
            limit=10
        )
        print(f"\nDirect search results count: {len(search_results)}")
        for i, result in enumerate(search_results):
            work_item = result.get("work_item", {})
            print(f"  {i+1}. ID: {work_item.get('id')}, Title: '{work_item.get('title')}'")
        
    except Exception as e:
        logger.error(f"Error in debug script: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'weaviate_manager' in locals():
            await weaviate_manager.stop()

if __name__ == "__main__":
    asyncio.run(debug_mcp_server_context())