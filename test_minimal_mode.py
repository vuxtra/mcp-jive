#!/usr/bin/env python3
"""Test script to verify minimal mode tool registration."""

import asyncio
import os
import sys
sys.path.insert(0, 'src')

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.ai_orchestrator import AIOrchestrator
from mcp_jive.config import AIConfig, ServerConfig
from mcp_jive.tools.registry import ToolRegistry

async def test_minimal_mode():
    """Test minimal mode tool registration."""
    print("Testing minimal mode tool registration...")
    
    # Set environment variable for minimal mode
    os.environ['MCP_TOOL_MODE'] = 'minimal'
    
    # Initialize components
    db_config = DatabaseConfig(
        data_path="./data/lancedb_jive",
        embedding_model="all-MiniLM-L6-v2",
        device="cpu"
    )
    
    ai_config = AIConfig(
        execution_mode="hybrid",
        default_provider="anthropic",
        enable_rate_limiting=False
    )
    
    server_config = ServerConfig()
    
    # Create instances
    db = LanceDBManager(db_config)
    await db.initialize()
    
    ai = AIOrchestrator(ai_config)
    
    # Create registry with tool_mode configuration
    from mcp_jive.config import Config
    config = Config()
    
    registry = ToolRegistry(database=db, ai_orchestrator=ai, config=config, lancedb_manager=db)
    await registry.initialize()
    
    # List registered tools
    tools = await registry.list_tools()
    print(f"\nRegistered {len(tools)} tools in minimal mode:")
    for i, tool in enumerate(tools, 1):
        print(f"{i:2d}. {tool.name}")
    
    # Check if we have the expected 16 tools
    expected_count = 16
    if len(tools) == expected_count:
        print(f"\n✅ SUCCESS: Minimal mode correctly registered {expected_count} tools")
    else:
        print(f"\n❌ ERROR: Expected {expected_count} tools, got {len(tools)}")
    
    # Check for core work item management tools
    work_item_tools = [tool.name for tool in tools if tool.name.startswith('jive_')]
    print(f"\nWork item management tools ({len(work_item_tools)}):")
    for tool in work_item_tools:
        print(f"  - {tool}")
    
    expected_work_tools = ['jive_create_work_item', 'jive_get_work_item', 'jive_update_work_item', 'jive_list_work_items', 'jive_search_work_items']
    missing_tools = [tool for tool in expected_work_tools if tool not in work_item_tools]
    if missing_tools:
        print(f"\n❌ Missing work item tools: {missing_tools}")
    else:
        print(f"\n✅ All 5 core work item tools present")

if __name__ == "__main__":
    asyncio.run(test_minimal_mode())