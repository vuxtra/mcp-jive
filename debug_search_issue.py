#!/usr/bin/env python3
"""Debug script to test search functionality directly."""

import asyncio
import logging
import os
from src.mcp_server.config import ServerConfig
from src.mcp_server.database import WeaviateManager
from src.mcp_server.utils.identifier_resolver import IdentifierResolver

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_search():
    """Test search functionality directly."""
    
    # Load config from .env.dev
    os.environ["MCP_JIVE_CONFIG"] = ".env.dev"
    config = ServerConfig()
    
    # Initialize Weaviate manager
    weaviate_manager = WeaviateManager(config)
    await weaviate_manager.start()
    
    print("\n=== Testing Direct Search ===")
    
    # Test direct search
    search_results = await weaviate_manager.search_work_items(
        query='"E-commerce Platform Modernization"',
        search_type="keyword",
        limit=10
    )
    
    print(f"Search returned {len(search_results)} results:")
    for i, result in enumerate(search_results):
        work_item = result.get("work_item", {})
        print(f"  {i+1}. ID: {work_item.get('id')}, Title: '{work_item.get('title')}'")
    
    print("\n=== Testing Identifier Resolver ===")
    
    # Test identifier resolver
    resolver = IdentifierResolver(weaviate_manager)
    resolved_id = await resolver.resolve_work_item_id("E-commerce Platform Modernization")
    
    print(f"Resolver returned: {resolved_id}")
    
    # Clean up
    await weaviate_manager.stop()

if __name__ == "__main__":
    asyncio.run(test_search())