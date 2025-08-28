"""Comprehensive fix for MCP SDK 1.13.1 tuple serialization bug.

This module provides complete monkey patches to fix the known issue where MCP objects
are incorrectly serialized as tuples during stdio transport, causing
'tuple' object has no attribute 'name' errors.

Root cause: Pydantic models have __iter__ methods that convert them to tuples
of (field_name, field_value) pairs, which breaks JSON serialization.

See: https://github.com/modelcontextprotocol/python-sdk/issues/987
"""

import logging
import json
from typing import Any, Dict, List
import inspect

logger = logging.getLogger(__name__)
PATCH_MARKER = "MCP_JIVE_FIX_MARKER_v6"


def apply_comprehensive_fixes():
    """Apply comprehensive fixes for MCP SDK serialization issues."""
    
    try:
        from mcp.types import Tool, ListToolsResult
        from mcp.server.lowlevel.server import Server
        import mcp.types
        
        # Check if we're in stdio mode by looking at environment variable
        import os
        is_stdio_mode = os.environ.get('MCP_JIVE_DEBUG', '').lower() != 'true'
        
        if not is_stdio_mode:
            logger.info("Applying comprehensive MCP serialization fixes")
        
        # Patch Tool.__iter__ to prevent tuple conversion
        if hasattr(Tool, '__iter__'):
            def patched_tool_iter(self):
                """Prevent tuple conversion by returning empty iterator."""
                return iter([])
            Tool.__iter__ = patched_tool_iter
            if not is_stdio_mode:
                logger.info("Patched Tool.__iter__")
        
        # Patch ListToolsResult.__iter__ to prevent tuple conversion
        if hasattr(ListToolsResult, '__iter__'):
            def patched_result_iter(self):
                """Prevent tuple conversion by returning empty iterator."""
                return iter([])
            ListToolsResult.__iter__ = patched_result_iter
            if not is_stdio_mode:
                logger.info("Patched ListToolsResult.__iter__")
        
        # Patch the MCP server's response serialization
        _patch_mcp_server_response_serialization()
        
        # Patch json.JSONEncoder for comprehensive handling
        _patch_json_encoder()
        
        if not is_stdio_mode:
            logger.warning(f"PROOF {PATCH_MARKER} - Comprehensive fixes applied")
        return True
        
    except Exception as e:
        # Always log errors, even in stdio mode, but use stderr
        logger.error(f"Failed to apply comprehensive fixes: {e}")
        return False


def _patch_mcp_server_response_serialization():
    """Patch the MCP server's response serialization to handle tools correctly."""
    
    try:
        from mcp.server.lowlevel.server import Server
        import mcp.server.lowlevel.server
        
        # Find and patch the response serialization methods
        if hasattr(Server, '_send_response'):
            original_send_response = Server._send_response
            
            def patched_send_response(self, request_id: Any, result: Any) -> None:
                """Patch response sending to handle tool serialization."""
                try:
                    # Ensure tools are properly serialized
                    if hasattr(result, 'tools') and result.tools:
                        logger.debug(f"Serializing {len(result.tools)} tools for response")
                        # Convert tools to dicts if they're still Pydantic models
                        serialized_tools = []
                        for tool in result.tools:
                            if hasattr(tool, 'model_dump'):
                                tool_dict = tool.model_dump(by_alias=True, mode="json", exclude_none=True)
                                serialized_tools.append(tool_dict)
                            else:
                                serialized_tools.append(tool)
                        
                        # Replace the tools list with serialized dicts
                        if hasattr(result, '__dict__'):
                            result.__dict__['tools'] = serialized_tools
                        else:
                            # Create new result with serialized tools
                            from mcp.types import ListToolsResult
                            result = ListToolsResult(tools=serialized_tools)
                    
                    return original_send_response(self, request_id, result)
                    
                except Exception as e:
                    logger.error(f"Error in patched response serialization: {e}")
                    return original_send_response(self, request_id, result)
            
            Server._send_response = patched_send_response
            logger.info("Patched Server._send_response for tool serialization")
            
    except Exception as e:
        logger.warning(f"Could not patch MCP server response serialization: {e}")


def _patch_json_encoder():
    """Patch JSON encoder to handle MCP types correctly."""
    
    try:
        import json
        from mcp.types import Tool
        
        # Store original encoder
        original_default = json.JSONEncoder.default
        
        def patched_default(self, obj):
            """Custom JSON encoder for MCP types."""
            
            # Handle Tool objects
            if isinstance(obj, Tool):
                return obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            
            # Handle ListToolsResult
            if hasattr(obj, 'tools') and hasattr(obj, 'model_dump'):
                result_dict = obj.model_dump(by_alias=True, mode="json", exclude_none=True)
                # Ensure tools are properly serialized
                if 'tools' in result_dict and result_dict['tools']:
                    serialized_tools = []
                    for tool in result_dict['tools']:
                        if isinstance(tool, dict):
                            serialized_tools.append(tool)
                        elif hasattr(tool, 'model_dump'):
                            serialized_tools.append(tool.model_dump(by_alias=True, mode="json", exclude_none=True))
                        else:
                            serialized_tools.append(tool)
                    result_dict['tools'] = serialized_tools
                return result_dict
            
            # Handle any Pydantic model
            if hasattr(obj, 'model_dump'):
                return obj.model_dump(by_alias=True, mode="json", exclude_none=True)
            
            # Fall back to original
            return original_default(self, obj)
        
        # Apply patch only once
        if not hasattr(json.JSONEncoder, '_mcp_jive_comprehensive_patched'):
            json.JSONEncoder.default = patched_default
            json.JSONEncoder._mcp_jive_comprehensive_patched = True
            logger.info("Applied comprehensive JSON encoder patch")
            
    except Exception as e:
        logger.warning(f"Could not patch JSON encoder: {e}")


def validate_tool_serialization(tools: List[Any]) -> List[Dict[str, Any]]:
    """Validate and ensure tools are properly serialized as dicts."""
    
    serialized_tools = []
    
    for i, tool in enumerate(tools):
        try:
            if hasattr(tool, 'model_dump'):
                tool_dict = tool.model_dump(by_alias=True, mode="json", exclude_none=True)
                serialized_tools.append(tool_dict)
                logger.debug(f"Tool {i}: {tool_dict.get('name', 'unknown')} serialized successfully")
            elif isinstance(tool, dict):
                serialized_tools.append(tool)
                logger.debug(f"Tool {i}: {tool.get('name', 'unknown')} already dict")
            else:
                logger.warning(f"Tool {i}: Unexpected type {type(tool)}")
                
        except Exception as e:
            logger.error(f"Error serializing tool {i}: {e}")
            
    return serialized_tools