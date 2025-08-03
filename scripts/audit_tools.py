#!/usr/bin/env python3
"""
MCP Tools Audit Script

This script audits all MCP tools to ensure they are properly implemented
and can handle basic function calls without errors.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_jive.config import load_config
from mcp_jive.lancedb_manager import LanceDBManager  # Migrated from Weaviate
from mcp_jive.tools.registry import MCPToolRegistry


class ToolAuditor:
    """Audits MCP tools for basic functionality."""
    
    def __init__(self):
        self.config = load_config()
        self.weaviate_manager = None
        self.registry = None
        self.results = {
            "total_tools": 0,
            "successful_tools": 0,
            "failed_tools": 0,
            "tool_results": {},
            "mode": self.config.tool_mode
        }
        
    async def initialize(self):
        """Initialize the auditor."""
        print(f"Initializing tool auditor in {self.config.tool_mode} mode...")
        
        # Initialize Weaviate
        self.weaviate_manager = WeaviateManager(self.config)
        await self.weaviate_manager.start()
        
        # Initialize tool registry
        self.registry = MCPToolRegistry(self.config, self.weaviate_manager)
        await self.registry.initialize()
        
        print(f"Initialized {len(self.registry.tools)} tools")
        
    async def audit_all_tools(self):
        """Audit all registered tools."""
        tools = await self.registry.list_tools()
        self.results["total_tools"] = len(tools)
        
        print(f"\nAuditing {len(tools)} tools...")
        print("=" * 50)
        
        for tool in tools:
            await self.audit_tool(tool)
            
        # Print summary
        self.print_summary()
        
    async def audit_tool(self, tool):
        """Audit a single tool."""
        tool_name = tool.name
        print(f"\nTesting {tool_name}...")
        
        try:
            # Get basic test arguments for the tool
            test_args = self.get_test_arguments(tool)
            
            # Try to call the tool
            result = await self.registry.call_tool(tool_name, test_args)
            
            # Check if result is valid
            if result and len(result) > 0:
                self.results["successful_tools"] += 1
                self.results["tool_results"][tool_name] = {
                    "status": "success",
                    "result_type": type(result[0]).__name__,
                    "result_length": len(result)
                }
                print(f"  ✅ {tool_name} - SUCCESS")
            else:
                self.results["failed_tools"] += 1
                self.results["tool_results"][tool_name] = {
                    "status": "failed",
                    "error": "Empty or invalid result"
                }
                print(f"  ❌ {tool_name} - FAILED (empty result)")
                
        except Exception as e:
            self.results["failed_tools"] += 1
            self.results["tool_results"][tool_name] = {
                "status": "error",
                "error": str(e)
            }
            print(f"  ❌ {tool_name} - ERROR: {str(e)[:100]}...")
            
    def get_test_arguments(self, tool) -> Dict[str, Any]:
        """Generate basic test arguments for a tool based on its schema."""
        schema = tool.inputSchema
        args = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                # Generate basic test values based on property type
                if prop_schema.get("type") == "string":
                    if "enum" in prop_schema:
                        args[prop_name] = prop_schema["enum"][0]
                    elif "id" in prop_name.lower():
                        args[prop_name] = "8a007a34-4a94-4346-a245-e04415f89ae7"
                    elif "path" in prop_name.lower():
                        args[prop_name] = "/tmp/test.json"
                    else:
                        args[prop_name] = "test-search-term"
                elif prop_schema.get("type") == "integer":
                    args[prop_name] = 1
                elif prop_schema.get("type") == "number":
                    args[prop_name] = 1.0
                elif prop_schema.get("type") == "boolean":
                    args[prop_name] = True
                elif prop_schema.get("type") == "array":
                    args[prop_name] = []
                elif prop_schema.get("type") == "object":
                    args[prop_name] = {}
                    
        return args
        
    def print_summary(self):
        """Print audit summary."""
        print("\n" + "=" * 50)
        print("AUDIT SUMMARY")
        print("=" * 50)
        print(f"Mode: {self.results['mode']}")
        print(f"Total Tools: {self.results['total_tools']}")
        print(f"Successful: {self.results['successful_tools']}")
        print(f"Failed: {self.results['failed_tools']}")
        
        success_rate = (self.results['successful_tools'] / self.results['total_tools']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tools
        if self.results['failed_tools'] > 0:
            print("\nFAILED TOOLS:")
            for tool_name, result in self.results['tool_results'].items():
                if result['status'] != 'success':
                    print(f"  - {tool_name}: {result.get('error', 'Unknown error')}")
                    
    async def cleanup(self):
        """Cleanup resources."""
        if self.weaviate_manager:
            await self.weaviate_manager.stop()
            

async def main():
    """Main audit function."""
    auditor = ToolAuditor()
    
    try:
        await auditor.initialize()
        await auditor.audit_all_tools()
        
        # Save results to file
        results_file = f"tool_audit_{auditor.config.tool_mode}_mode.json"
        with open(results_file, 'w') as f:
            json.dump(auditor.results, f, indent=2)
        print(f"\nResults saved to {results_file}")
        
    except Exception as e:
        print(f"Audit failed: {e}")
        return 1
    finally:
        await auditor.cleanup()
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)