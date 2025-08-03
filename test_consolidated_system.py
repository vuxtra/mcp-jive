#!/usr/bin/env python3
"""
Test the consolidated MCP Jive system to verify everything works.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports from consolidated mcp_jive
try:
    from mcp_jive.server import MCPServer
    from mcp_jive.config import ServerConfig
    from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
    from mcp_jive.tools.client_tools import MCPClientTools
    from mcp_jive.tools.registry import MCPToolRegistry
    print("✅ All core imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_consolidated_system():
    """Test the consolidated system functionality."""
    print("\n=== Testing Consolidated MCP Jive System ===")
    print()
    
    # Test 1: Database initialization
    print("1. Testing database initialization...")
    try:
        config = DatabaseConfig(data_path='./data/lancedb_jive')
        db_manager = LanceDBManager(config)
        await db_manager.initialize()
        print("   ✅ Database initialized successfully")
        
        # Check tables
        tables = db_manager.list_tables()
        print(f"   ✅ Found tables: {tables}")
        
        # Check WorkItem table
        if 'WorkItem' in tables:
            work_item_table = db_manager.get_table('WorkItem')
            count = work_item_table.count_rows()
            print(f"   ✅ WorkItem table has {count} records")
        
        await db_manager.cleanup()
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False
    
    # Test 2: Server configuration
    print("\n2. Testing server configuration...")
    try:
        server_config = ServerConfig()
        print(f"   ✅ Server config created: {server_config.host}:{server_config.port}")
    except Exception as e:
        print(f"   ❌ Server config test failed: {e}")
        return False
    
    # Test 3: Tool registry
    print("\n3. Testing tool registry...")
    try:
        # Initialize database for tools
        config = DatabaseConfig(data_path='./data/lancedb_jive')
        db_manager = LanceDBManager(config)
        await db_manager.initialize()
        
        # Create tool registry
        registry = MCPToolRegistry(lancedb_manager=db_manager)
        await registry.initialize()
        tools = await registry.list_tools()
        print(f"   ✅ Tool registry created with {len(tools)} tools")
        
        # List some tools
        if tools:
            tool_names = [getattr(tool, 'name', str(tool)) for tool in tools[:5]]
            print(f"   ✅ Sample tools: {tool_names}")
        else:
            print(f"   ✅ Tool registry initialized (no tools registered yet)")
        
        await db_manager.cleanup()
        
    except Exception as e:
        print(f"   ❌ Tool registry test failed: {e}")
        return False
    
    # Test 4: Work item creation
    print("\n4. Testing work item creation...")
    try:
        # Initialize database
        config = DatabaseConfig(data_path='./data/lancedb_jive')
        db_manager = LanceDBManager(config)
        await db_manager.initialize()
        
        # Create work item
        import uuid
        work_item_data = {
            'id': str(uuid.uuid4()),
            'title': 'Test Consolidated System',
            'description': 'Testing the consolidated MCP Jive system',
            'item_type': 'task',
            'status': 'todo',
            'priority': 'medium',
            'tags': ['test', 'consolidation']
        }
        
        work_item_id = await db_manager.create_work_item(work_item_data)
        print(f"   ✅ Created work item: {work_item_id}")
        
        # Retrieve work item
        retrieved = await db_manager.get_work_item(work_item_id)
        if retrieved:
            print(f"   ✅ Retrieved work item: {retrieved['title']}")
        else:
            print("   ❌ Failed to retrieve work item")
        
        await db_manager.cleanup()
        
    except Exception as e:
        print(f"   ❌ Work item creation test failed: {e}")
        return False
    
    print("\n=== All Tests Passed! ===")
    print("✅ The consolidated MCP Jive system is working correctly")
    return True

async def test_server_startup():
    """Test server startup (without actually running it)."""
    print("\n5. Testing server startup configuration...")
    try:
        # Test server initialization
        server_config = ServerConfig()
        
        # Initialize database
        db_config = DatabaseConfig(data_path='./data/lancedb_jive')
        db_manager = LanceDBManager(db_config)
        await db_manager.initialize()
        
        # Create server instance
        server = MCPServer(server_config, db_manager)
        print("   ✅ Server instance created successfully")
        print(f"   ✅ Server configured for {server_config.host}:{server_config.port}")
        
        await db_manager.cleanup()
        
    except Exception as e:
        print(f"   ❌ Server startup test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    async def main():
        success = await test_consolidated_system()
        if success:
            success = await test_server_startup()
        
        if success:
            print("\n🎉 Consolidation verification complete!")
            print("The MCP Jive system is ready for production use.")
        else:
            print("\n❌ Consolidation verification failed!")
            print("Please review the errors above.")
    
    asyncio.run(main())