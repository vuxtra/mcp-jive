#!/usr/bin/env python3
"""
Detailed MCP Tools Audit Script

This script provides a more thorough audit of MCP tools, analyzing the actual
content of responses to identify errors and issues that may be hidden by
successful response wrapping.
"""

import asyncio
import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_jive.config import load_config
from mcp_jive.lancedb_manager import LanceDBManager  # Migrated from Weaviate
from mcp_jive.tools.registry import MCPToolRegistry


class DetailedToolAuditor:
    """Provides detailed audit of MCP tools with error analysis."""
    
    def __init__(self):
        self.config = load_config()
        self.weaviate_manager = None
        self.registry = None
        self.results = {
            "total_tools": 0,
            "truly_successful_tools": 0,
            "tools_with_errors": 0,
            "completely_failed_tools": 0,
            "tool_details": {},
            "mode": self.config.tool_mode,
            "error_patterns": {
                "database_errors": [],
                "validation_errors": [],
                "uuid_errors": [],
                "schema_errors": [],
                "other_errors": []
            }
        }
        
    async def initialize(self):
        """Initialize the auditor."""
        print(f"Initializing detailed tool auditor in {self.config.tool_mode} mode...")
        
        # Initialize Weaviate
        self.weaviate_manager = WeaviateManager(self.config)
        await self.weaviate_manager.start()
        
        # Initialize tool registry
        self.registry = MCPToolRegistry(self.config, self.weaviate_manager)
        await self.registry.initialize()
        
        print(f"Initialized {len(self.registry.tools)} tools")
        
    async def audit_all_tools(self):
        """Audit all registered tools with detailed analysis."""
        tools = await self.registry.list_tools()
        self.results["total_tools"] = len(tools)
        
        print(f"\nDetailed auditing of {len(tools)} tools...")
        print("=" * 60)
        
        for tool in tools:
            await self.audit_tool_detailed(tool)
            
        # Print detailed summary
        self.print_detailed_summary()
        
    async def audit_tool_detailed(self, tool):
        """Perform detailed audit of a single tool."""
        tool_name = tool.name
        print(f"\n🔍 Testing {tool_name}...")
        
        try:
            # Get test arguments
            test_args = self.get_test_arguments(tool)
            
            # Capture logs during tool execution
            import logging
            import io
            
            # Create a string buffer to capture logs
            log_capture = io.StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.ERROR)
            
            # Add handler to capture errors
            root_logger = logging.getLogger()
            original_level = root_logger.level
            root_logger.addHandler(handler)
            
            try:
                # Call the tool
                result = await self.registry.call_tool(tool_name, test_args)
                
                # Get captured logs
                log_output = log_capture.getvalue()
                
                # Analyze the result and logs
                analysis = self.analyze_tool_result(tool_name, result, log_output)
                
                self.results["tool_details"][tool_name] = analysis
                
                # Update counters
                if analysis["status"] == "success":
                    self.results["truly_successful_tools"] += 1
                    print(f"  ✅ {tool_name} - TRUE SUCCESS")
                elif analysis["status"] == "error_but_functional":
                    self.results["tools_with_errors"] += 1
                    print(f"  ⚠️  {tool_name} - FUNCTIONAL BUT HAS ERRORS")
                    print(f"     Errors: {', '.join(analysis['error_types'])}")
                else:
                    self.results["completely_failed_tools"] += 1
                    print(f"  ❌ {tool_name} - FAILED")
                    print(f"     Error: {analysis.get('error', 'Unknown error')}")
                    
            finally:
                # Clean up logging
                root_logger.removeHandler(handler)
                root_logger.setLevel(original_level)
                handler.close()
                
        except Exception as e:
            self.results["completely_failed_tools"] += 1
            self.results["tool_details"][tool_name] = {
                "status": "exception",
                "error": str(e),
                "error_types": ["exception"]
            }
            print(f"  💥 {tool_name} - EXCEPTION: {str(e)[:100]}...")
            
    def analyze_tool_result(self, tool_name: str, result: List[Any], log_output: str) -> Dict[str, Any]:
        """Analyze tool result and logs to determine actual status."""
        analysis = {
            "has_result": bool(result and len(result) > 0),
            "result_count": len(result) if result else 0,
            "has_log_errors": bool(log_output.strip()),
            "log_errors": log_output.strip() if log_output.strip() else None,
            "error_types": [],
            "status": "unknown"
        }
        
        # Check for specific error patterns in logs
        if log_output:
            error_types = []
            
            if "reserved property name" in log_output:
                error_types.append("reserved_property")
                self.results["error_patterns"]["schema_errors"].append(tool_name)
                
            if "Not valid 'uuid'" in log_output:
                error_types.append("invalid_uuid")
                self.results["error_patterns"]["uuid_errors"].append(tool_name)
                
            if "Query call with protocol GRPC" in log_output:
                error_types.append("grpc_query_error")
                self.results["error_patterns"]["database_errors"].append(tool_name)
                
            if "object has no attribute" in log_output:
                error_types.append("attribute_error")
                self.results["error_patterns"]["database_errors"].append(tool_name)
                
            if "422 Unprocessable Entity" in log_output:
                error_types.append("validation_error")
                self.results["error_patterns"]["validation_errors"].append(tool_name)
                
            if "RFC3339 formatted date" in log_output:
                error_types.append("date_format_error")
                self.results["error_patterns"]["validation_errors"].append(tool_name)
                
            if not error_types:
                error_types.append("unknown_error")
                self.results["error_patterns"]["other_errors"].append(tool_name)
                
            analysis["error_types"] = error_types
        
        # Determine overall status
        if not analysis["has_result"]:
            analysis["status"] = "failed_no_result"
        elif not analysis["has_log_errors"]:
            analysis["status"] = "success"
        else:
            # Has result but also has errors - functional but problematic
            analysis["status"] = "error_but_functional"
            
        return analysis
        
    def get_test_arguments(self, tool) -> Dict[str, Any]:
        """Generate test arguments for a tool."""
        schema = tool.inputSchema
        args = {}
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_schema.get("type") == "string":
                    if "enum" in prop_schema:
                        args[prop_name] = prop_schema["enum"][0]
                    elif "id" in prop_name.lower():
                        args[prop_name] = "9a2ef31d-f4c3-4057-885f-1903d5fb4a65"
                    elif "path" in prop_name.lower():
                        args[prop_name] = "/tmp/test.json"
                    else:
                        args[prop_name] = "test-search-term"
                elif prop_schema.get("type") == "integer":
                    args[prop_name] = 1
                elif prop_schema.get("type") == "boolean":
                    args[prop_name] = True
                elif prop_schema.get("type") == "array":
                    args[prop_name] = ["test-item"]
                elif prop_schema.get("type") == "object":
                    args[prop_name] = {"test": "value"}
                    
        return args
        
    def print_detailed_summary(self):
        """Print detailed audit summary."""
        print("\n" + "=" * 60)
        print("📊 DETAILED AUDIT SUMMARY")
        print("=" * 60)
        
        total = self.results["total_tools"]
        success = self.results["truly_successful_tools"]
        errors = self.results["tools_with_errors"]
        failed = self.results["completely_failed_tools"]
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tools: {total}")
        print(f"   ✅ Truly Successful: {success} ({success/total*100:.1f}%)")
        print(f"   ⚠️  Functional with Errors: {errors} ({errors/total*100:.1f}%)")
        print(f"   ❌ Completely Failed: {failed} ({failed/total*100:.1f}%)")
        
        print(f"\n🔍 Error Pattern Analysis:")
        for pattern, tools in self.results["error_patterns"].items():
            if tools:
                print(f"   {pattern.replace('_', ' ').title()}: {len(tools)} tools")
                print(f"      Tools: {', '.join(tools[:5])}{'...' if len(tools) > 5 else ''}")
        
        # Save detailed results
        output_file = f"detailed_audit_{self.results['mode']}_mode.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    async def cleanup(self):
        """Clean up resources."""
        if self.weaviate_manager:
            await self.weaviate_manager.stop()


async def main():
    """Main audit function."""
    auditor = DetailedToolAuditor()
    
    try:
        await auditor.initialize()
        await auditor.audit_all_tools()
        return 0
    except Exception as e:
        print(f"Audit failed: {e}")
        return 1
    finally:
        await auditor.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)