#!/bin/bash

# MCP Jive Server - Consolidated Tools Only
# This script runs the server with only the 7 consolidated tools
# and disables AI functionality to avoid API key requirements

echo "Starting MCP Jive Server with consolidated tools only..."
echo "Configuration:"
echo "  - Tool Mode: consolidated (7 tools)"
echo "  - AI Execution Mode: mcp_client (no API keys required)"
echo "  - Legacy Support: disabled"
echo ""

# Set environment variables
# MCP_JIVE_TOOL_MODE no longer needed - using consolidated tools by default
export AI_EXECUTION_MODE=mcp_client

# Start the server
./bin/mcp-jive server start --mode stdio