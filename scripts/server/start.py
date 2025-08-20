#!/usr/bin/env python3
"""
MCP Jive Server Starter

Unified server startup script with support for different modes and configurations.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    parser = argparse.ArgumentParser(
        description="Start MCP Jive Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode stdio                    # Start in stdio mode (default)
  %(prog)s --mode http --port 8080         # Start HTTP server on port 8080
  %(prog)s --mode combined --port 3454     # Start combined HTTP+WebSocket server
  %(prog)s --consolidated                  # Use only consolidated tools
  %(prog)s --debug                         # Enable debug logging
"""
    )
    
    parser.add_argument("--mode", choices=["stdio", "http", "websocket", "combined"], 
                       default="stdio", help="Server mode (default: stdio)")
    parser.add_argument("--port", type=int, default=3454, 
                       help="Port for HTTP/WebSocket mode (default: 3454)")
    parser.add_argument("--host", default="localhost", 
                       help="Host for HTTP/WebSocket mode (default: localhost)")
    parser.add_argument("--consolidated", action="store_true",
                       help="Use consolidated tools only (7 tools)")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO", help="Set logging level")
    parser.add_argument("--config", type=str,
                       help="Path to configuration file")
    parser.add_argument("--db-path", type=str,
                       help="Path to LanceDB database directory")
    
    args = parser.parse_args()
    
    # Prepare environment variables
    env = os.environ.copy()
    
    if args.consolidated:
        # Set environment variables for consolidated mode
        env["MCP_JIVE_CONSOLIDATED_TOOLS"] = "true"
        env["MCP_JIVE_AI_ENABLED"] = "false"
        env["MCP_JIVE_TOOL_COUNT"] = "7"
        print("Starting MCP Jive Server in consolidated mode (7 tools, AI disabled)")
    else:
        print("Starting MCP Jive Server in full mode")
    
    if args.debug:
        env["MCP_JIVE_DEBUG"] = "true"
        env["MCP_JIVE_LOG_LEVEL"] = "DEBUG"
    else:
        env["MCP_JIVE_LOG_LEVEL"] = args.log_level
    
    if args.config:
        env["MCP_JIVE_CONFIG_PATH"] = args.config
    
    if args.db_path:
        env["LANCEDB_DATA_PATH"] = args.db_path
        print(f"Using custom database path: {args.db_path}")
    
    # Prepare command
    main_script = project_root / "mcp-server.py"
    if not main_script.exists():
        # Fallback to src/main.py
        main_script = project_root / "src" / "main.py"
    
    if not main_script.exists():
        print("Error: Main server script not found")
        return 1
    
    cmd = [sys.executable, str(main_script)]
    
    # Add mode-specific arguments
    if args.mode:
        cmd.append(args.mode)  # mcp-server.py expects mode as positional argument
    
    if args.mode in ["http", "websocket"]:
        cmd.extend(["--port", str(args.port)])
        cmd.extend(["--host", args.host])
    
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
    
    try:
        print(f"Command: {' '.join(cmd)}")
        print(f"Mode: {args.mode}")
        if args.mode in ["http", "websocket"]:
            print(f"Address: {args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        result = subprocess.run(cmd, env=env)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())