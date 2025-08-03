#!/usr/bin/env python3
"""Test script to verify full mode tool registration.

This script tests that full mode registers the expected 35+ tools
as specified in TOOL_MODE_IMPLEMENTATION.md.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from mcp_jive.config import Config
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.ai_orchestrator import AIOrchestrator
from mcp_jive.tools.registry import ToolRegistry

async def test_full_mode():
    """Test full mode tool registration."""
    print("Testing full mode tool registration...")
    
    # Set environment to full mode
    os.environ["MCP_TOOL_MODE"] = "full"
    
    try:
        # Initialize components
        config = Config()
        
        # Create proper DatabaseConfig for LanceDBManager
        db_config = DatabaseConfig(
            data_path=config.database.lancedb_data_path,
            embedding_model=config.database.lancedb_embedding_model,
            device=config.database.lancedb_device
        )
        db = LanceDBManager(db_config)
        await db.initialize()
        
        ai_orchestrator = AIOrchestrator(config.ai)
        
        # Initialize tool registry with full mode
        registry = ToolRegistry(
            database=None,
            ai_orchestrator=ai_orchestrator,
            config=config,
            lancedb_manager=db
        )
        
        # Initialize and register tools
        await registry.initialize()
        
        # Get registered tools
        tools = await registry.list_tools()
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in tools]
        tool_names.sort()
        
        print(f"\n📊 Full mode registered {len(tools)} tools:")
        for tool_name in tool_names:
            print(f"   - {tool_name}")
        
        # Verify we have 35+ tools
        if len(tools) >= 35:
            print(f"\n✅ Full mode successfully registered {len(tools)} tools (expected 35+)")
        else:
            print(f"\n❌ Full mode only registered {len(tools)} tools (expected 35+)")
            return False
        
        # Categorize tools
        work_item_tools = [name for name in tool_names if name.startswith('jive_') and any(keyword in name for keyword in ['work_item', 'create', 'get', 'update', 'list', 'search'])]
        hierarchy_tools = [name for name in tool_names if name.startswith('jive_') and any(keyword in name for keyword in ['children', 'dependencies', 'hierarchy'])]
        workflow_tools = [name for name in tool_names if name.startswith('jive_') and any(keyword in name for keyword in ['execute', 'workflow', 'cancel'])]
        storage_tools = [name for name in tool_names if name.startswith('jive_') and any(keyword in name for keyword in ['sync', 'storage'])]
        validation_tools = [name for name in tool_names if name.startswith('jive_') and any(keyword in name for keyword in ['validate', 'quality', 'approve'])]
        ai_tools = [name for name in tool_names if name.startswith('ai_')]
        
        print(f"\nTool Categories:")
        print(f"Work Item Management tools ({len(work_item_tools)}):")
        for tool in work_item_tools:
            print(f"  - {tool}")
        
        print(f"\nHierarchy Management tools ({len(hierarchy_tools)}):")
        for tool in hierarchy_tools:
            print(f"  - {tool}")
        
        print(f"\nWorkflow Execution tools ({len(workflow_tools)}):")
        for tool in workflow_tools:
            print(f"  - {tool}")
        
        print(f"\nStorage Sync tools ({len(storage_tools)}):")
        for tool in storage_tools:
            print(f"  - {tool}")
        
        print(f"\nValidation tools ({len(validation_tools)}):")
        for tool in validation_tools:
            print(f"  - {tool}")
        
        print(f"\nAI Orchestration tools ({len(ai_tools)}):")
        for tool in ai_tools:
            print(f"  - {tool}")
        
        # Verify core tools are present
        core_tools = ['jive_create_work_item', 'jive_get_work_item', 'jive_update_work_item', 'jive_list_work_items', 'jive_search_work_items']
        missing_core = [tool for tool in core_tools if tool not in tool_names]
        
        if missing_core:
            print(f"\n❌ Missing core tools: {missing_core}")
            return False
        else:
            print(f"\n✅ All {len(core_tools)} core work item tools present")
        
        return True
        
    except Exception as e:
        print(f"Failed to initialize tool registry: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_mode())
    sys.exit(0 if success else 1)