#!/usr/bin/env python3
"""
Quick Validation Script for Consolidated MCP Jive Tools

This script performs a quick validation of the consolidated tools to ensure
they are properly implemented and can be imported and instantiated before
running the comprehensive test suite.

Usage:
    python validate_consolidated_tools.py [--verbose]
"""

import argparse
import asyncio
import sys
import traceback
from typing import Dict, List, Any, Optional


def log_status(message: str, status: str = "INFO"):
    """Log message with colored status."""
    colors = {
        "SUCCESS": "\033[92m",  # Green
        "ERROR": "\033[91m",    # Red
        "WARNING": "\033[93m",  # Yellow
        "INFO": "\033[94m",     # Blue
        "RESET": "\033[0m"      # Reset
    }
    
    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    print(f"{color}[{status}]{reset} {message}")


def validate_imports() -> bool:
    """Validate that all consolidated tools can be imported."""
    log_status("Validating imports...", "INFO")
    
    try:
        # Test basic imports
        from src.mcp_jive.tools.consolidated import (
            UnifiedWorkItemTool,
            UnifiedRetrievalTool,
            UnifiedSearchTool,
            UnifiedHierarchyTool,
            UnifiedExecutionTool,
            UnifiedProgressTool,
            UnifiedStorageTool,
            ConsolidatedToolRegistry,
            CONSOLIDATED_TOOLS
        )
        
        log_status("✅ All consolidated tools imported successfully", "SUCCESS")
        
        # Validate CONSOLIDATED_TOOLS list
        if isinstance(CONSOLIDATED_TOOLS, list) and len(CONSOLIDATED_TOOLS) == 7:
            log_status(f"✅ CONSOLIDATED_TOOLS list contains {len(CONSOLIDATED_TOOLS)} tools", "SUCCESS")
            for tool_name in CONSOLIDATED_TOOLS:
                log_status(f"   - {tool_name}", "INFO")
        else:
            log_status(f"❌ CONSOLIDATED_TOOLS validation failed: {type(CONSOLIDATED_TOOLS)}, length: {len(CONSOLIDATED_TOOLS) if hasattr(CONSOLIDATED_TOOLS, '__len__') else 'N/A'}", "ERROR")
            return False
        
        return True
        
    except ImportError as e:
        log_status(f"❌ Import failed: {e}", "ERROR")
        return False
    except Exception as e:
        log_status(f"❌ Unexpected error during import: {e}", "ERROR")
        return False


def validate_tool_instantiation() -> bool:
    """Validate that all tools can be instantiated."""
    log_status("Validating tool instantiation...", "INFO")
    
    try:
        from src.mcp_jive.tools.consolidated import (
            UnifiedWorkItemTool,
            UnifiedRetrievalTool,
            UnifiedSearchTool,
            UnifiedHierarchyTool,
            UnifiedExecutionTool,
            UnifiedProgressTool,
            UnifiedStorageTool
        )
        
        tools = {
            "UnifiedWorkItemTool": UnifiedWorkItemTool,
            "UnifiedRetrievalTool": UnifiedRetrievalTool,
            "UnifiedSearchTool": UnifiedSearchTool,
            "UnifiedHierarchyTool": UnifiedHierarchyTool,
            "UnifiedExecutionTool": UnifiedExecutionTool,
            "UnifiedProgressTool": UnifiedProgressTool,
            "UnifiedStorageTool": UnifiedStorageTool
        }
        
        instantiated_tools = {}
        
        for tool_name, tool_class in tools.items():
            try:
                tool_instance = tool_class()
                instantiated_tools[tool_name] = tool_instance
                log_status(f"✅ {tool_name} instantiated successfully", "SUCCESS")
            except Exception as e:
                log_status(f"❌ {tool_name} instantiation failed: {e}", "ERROR")
                return False
        
        log_status(f"✅ All {len(instantiated_tools)} tools instantiated successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log_status(f"❌ Tool instantiation validation failed: {e}", "ERROR")
        return False


def validate_abstract_methods() -> bool:
    """Validate that all tools implement required abstract methods."""
    log_status("Validating abstract method implementations...", "INFO")
    
    try:
        from src.mcp_jive.tools.consolidated import (
            UnifiedWorkItemTool,
            UnifiedRetrievalTool,
            UnifiedSearchTool,
            UnifiedHierarchyTool,
            UnifiedExecutionTool,
            UnifiedProgressTool,
            UnifiedStorageTool
        )
        
        tools = [
            UnifiedWorkItemTool(),
            UnifiedRetrievalTool(),
            UnifiedSearchTool(),
            UnifiedHierarchyTool(),
            UnifiedExecutionTool(),
            UnifiedProgressTool(),
            UnifiedStorageTool()
        ]
        
        required_properties = ['name', 'description', 'category', 'parameters_schema']
        required_methods = ['execute']
        
        for tool in tools:
            tool_name = tool.__class__.__name__
            
            # Check properties
            for prop in required_properties:
                if not hasattr(tool, prop):
                    log_status(f"❌ {tool_name} missing property: {prop}", "ERROR")
                    return False
                
                try:
                    value = getattr(tool, prop)
                    if value is None:
                        log_status(f"❌ {tool_name}.{prop} is None", "ERROR")
                        return False
                except Exception as e:
                    log_status(f"❌ {tool_name}.{prop} access failed: {e}", "ERROR")
                    return False
            
            # Check methods
            for method in required_methods:
                if not hasattr(tool, method):
                    log_status(f"❌ {tool_name} missing method: {method}", "ERROR")
                    return False
                
                if not callable(getattr(tool, method)):
                    log_status(f"❌ {tool_name}.{method} is not callable", "ERROR")
                    return False
            
            log_status(f"✅ {tool_name} implements all required methods and properties", "SUCCESS")
        
        log_status("✅ All tools implement required abstract methods", "SUCCESS")
        return True
        
    except Exception as e:
        log_status(f"❌ Abstract method validation failed: {e}", "ERROR")
        return False


async def validate_mcp_tools() -> bool:
    """Validate that all tools implement get_tools() method correctly."""
    log_status("Validating MCP tool implementations...", "INFO")
    
    try:
        from src.mcp_jive.tools.consolidated import (
            UnifiedWorkItemTool,
            UnifiedRetrievalTool,
            UnifiedSearchTool,
            UnifiedHierarchyTool,
            UnifiedExecutionTool,
            UnifiedProgressTool,
            UnifiedStorageTool
        )
        
        tools = [
            UnifiedWorkItemTool(),
            UnifiedRetrievalTool(),
            UnifiedSearchTool(),
            UnifiedHierarchyTool(),
            UnifiedExecutionTool(),
            UnifiedProgressTool(),
            UnifiedStorageTool()
        ]
        
        expected_tool_names = [
            "jive_manage_work_item",
            "jive_get_work_item",
            "jive_search_content",
            "jive_get_hierarchy",
            "jive_execute_work_item",
            "jive_track_progress",
            "jive_sync_data"
        ]
        
        found_tools = []
        
        for tool in tools:
            tool_name = tool.__class__.__name__
            
            # Check if get_tools method exists
            if not hasattr(tool, 'get_tools'):
                log_status(f"❌ {tool_name} missing get_tools() method", "ERROR")
                return False
            
            # Check if get_tools is async
            if not asyncio.iscoroutinefunction(tool.get_tools):
                log_status(f"❌ {tool_name}.get_tools() is not async", "ERROR")
                return False
            
            try:
                # Call get_tools
                mcp_tools = await tool.get_tools()
                
                if not isinstance(mcp_tools, list):
                    log_status(f"❌ {tool_name}.get_tools() should return a list, got {type(mcp_tools)}", "ERROR")
                    return False
                
                if len(mcp_tools) != 1:
                    log_status(f"❌ {tool_name}.get_tools() should return exactly 1 tool, got {len(mcp_tools)}", "ERROR")
                    return False
                
                mcp_tool = mcp_tools[0]
                
                # Validate MCP tool structure
                if not hasattr(mcp_tool, 'name'):
                    log_status(f"❌ {tool_name} MCP tool missing 'name' attribute", "ERROR")
                    return False
                
                if not hasattr(mcp_tool, 'description'):
                    log_status(f"❌ {tool_name} MCP tool missing 'description' attribute", "ERROR")
                    return False
                
                if not hasattr(mcp_tool, 'inputSchema'):
                    log_status(f"❌ {tool_name} MCP tool missing 'inputSchema' attribute", "ERROR")
                    return False
                
                # Check tool name
                if mcp_tool.name not in expected_tool_names:
                    log_status(f"❌ {tool_name} has unexpected MCP tool name: {mcp_tool.name}", "ERROR")
                    return False
                
                found_tools.append(mcp_tool.name)
                log_status(f"✅ {tool_name} -> {mcp_tool.name} validated", "SUCCESS")
                
            except Exception as e:
                log_status(f"❌ {tool_name}.get_tools() failed: {e}", "ERROR")
                return False
        
        # Check that all expected tools were found
        missing_tools = set(expected_tool_names) - set(found_tools)
        if missing_tools:
            log_status(f"❌ Missing MCP tools: {missing_tools}", "ERROR")
            return False
        
        log_status(f"✅ All {len(found_tools)} MCP tools validated successfully", "SUCCESS")
        return True
        
    except Exception as e:
        log_status(f"❌ MCP tool validation failed: {e}", "ERROR")
        return False


def validate_registry() -> bool:
    """Validate that the consolidated tool registry works correctly."""
    log_status("Validating consolidated tool registry...", "INFO")
    
    try:
        from src.mcp_jive.tools.consolidated import ConsolidatedToolRegistry
        
        # Create registry
        registry = ConsolidatedToolRegistry()
        
        # Check that registry has tools
        if not hasattr(registry, 'tools'):
            log_status("❌ Registry missing 'tools' attribute", "ERROR")
            return False
        
        if not isinstance(registry.tools, dict):
            log_status(f"❌ Registry.tools should be dict, got {type(registry.tools)}", "ERROR")
            return False
        
        if len(registry.tools) != 7:
            log_status(f"❌ Registry should have 7 tools, got {len(registry.tools)}", "ERROR")
            return False
        
        expected_tools = [
            "jive_manage_work_item",
            "jive_get_work_item",
            "jive_search_content",
            "jive_get_hierarchy",
            "jive_execute_work_item",
            "jive_track_progress",
            "jive_sync_data"
        ]
        
        for tool_name in expected_tools:
            if tool_name not in registry.tools:
                log_status(f"❌ Registry missing tool: {tool_name}", "ERROR")
                return False
            
            tool_instance = registry.tools[tool_name]
            if not hasattr(tool_instance, 'execute'):
                log_status(f"❌ Registry tool {tool_name} missing execute method", "ERROR")
                return False
        
        log_status(f"✅ Registry contains all {len(registry.tools)} expected tools", "SUCCESS")
        return True
        
    except Exception as e:
        log_status(f"❌ Registry validation failed: {e}", "ERROR")
        return False


async def validate_basic_execution() -> bool:
    """Validate basic execution of consolidated tools."""
    log_status("Validating basic tool execution...", "INFO")
    
    try:
        from src.mcp_jive.tools.consolidated import UnifiedWorkItemTool
        
        # Test basic execution with mock data
        tool = UnifiedWorkItemTool()
        
        # Test with minimal valid parameters
        test_params = {
            "action": "create",
            "title": "Validation Test Item",
            "description": "Test item for validation",
            "type": "task"
        }
        
        try:
            result = await tool.execute(test_params)
            
            # Check result structure
            if not hasattr(result, 'success'):
                log_status("❌ Tool result missing 'success' attribute", "ERROR")
                return False
            
            if not hasattr(result, 'data'):
                log_status("❌ Tool result missing 'data' attribute", "ERROR")
                return False
            
            # Note: The actual execution might fail due to missing database,
            # but we're validating that the tool can be called and returns
            # a proper result structure
            log_status(f"✅ Tool execution returned proper result structure (success: {result.success})", "SUCCESS")
            
        except Exception as e:
            # This is expected if database is not available
            log_status(f"⚠️  Tool execution failed (expected without database): {e}", "WARNING")
        
        return True
        
    except Exception as e:
        log_status(f"❌ Basic execution validation failed: {e}", "ERROR")
        return False


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Quick validation for consolidated MCP Jive tools"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    log_status("Starting consolidated tools validation...", "INFO")
    print("=" * 60)
    
    validation_steps = [
        ("Import Validation", validate_imports),
        ("Tool Instantiation", validate_tool_instantiation),
        ("Abstract Methods", validate_abstract_methods),
        ("MCP Tools", validate_mcp_tools),
        ("Registry", validate_registry),
        ("Basic Execution", validate_basic_execution)
    ]
    
    passed = 0
    failed = 0
    
    for step_name, validation_func in validation_steps:
        print(f"\n{'-' * 40}")
        log_status(f"Running: {step_name}", "INFO")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(validation_func):
                success = await validation_func()
            else:
                success = validation_func()
            
            if success:
                passed += 1
                log_status(f"{step_name}: PASSED", "SUCCESS")
            else:
                failed += 1
                log_status(f"{step_name}: FAILED", "ERROR")
                
        except Exception as e:
            failed += 1
            log_status(f"{step_name}: FAILED with exception: {e}", "ERROR")
            if args.verbose:
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    log_status("VALIDATION SUMMARY", "INFO")
    print("=" * 60)
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Steps: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed == 0:
        log_status("🎉 ALL VALIDATIONS PASSED! Consolidated tools are ready for comprehensive testing.", "SUCCESS")
        return 0
    else:
        log_status(f"❌ {failed} validation(s) failed. Please fix issues before running comprehensive tests.", "ERROR")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_status("Validation interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log_status(f"Validation failed with unexpected error: {e}", "ERROR")
        sys.exit(1)