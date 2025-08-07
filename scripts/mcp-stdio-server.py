#!/usr/bin/env python3
"""
MCP Jive Server - STDIO Mode for MCP Client Integration

This script runs the MCP Jive server in stdio mode specifically for MCP client integration.
It uses the latest code and ensures proper stdio transport for IDE extensions.

Usage:
    python scripts/mcp-stdio-server.py [options]
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import and run main
if __name__ == "__main__":
    # Set stdio mode arguments
    sys.argv = ["main.py", "--stdio"]
    
    # Set development environment
    os.environ['MCP_JIVE_ENV'] = 'development'
    os.environ['MCP_JIVE_DEBUG'] = 'true'
    os.environ['MCP_LOG_LEVEL'] = 'INFO'
    
    # Import and run main
    from main import main
    main()