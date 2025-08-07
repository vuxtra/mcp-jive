#!/usr/bin/env python3
"""Unified MCP Jive Server Entry Point.

This is the single, unified entry point for the MCP Jive server that replaces
all the scattered startup scripts with a clean, flag-based interface.

Usage:
    python mcp-server.py [mode] [options]

Modes:
    stdio       Run in stdio mode for MCP client integration (default)
    http        Run in HTTP mode for web API access
    websocket   Run in WebSocket mode for real-time communication
    dev         Run in development mode with hot-reload

Options:
    --host HOST         Server host address (default: localhost)
    --port PORT         Server port number (default: 3456)
    --debug             Enable debug mode with verbose logging
    --log-level LEVEL   Set logging level (DEBUG, INFO, WARNING, ERROR)
    --config FILE       Path to configuration file
    --no-reload         Disable auto-reload in dev mode
    --help              Show this help message

Examples:
    python mcp-server.py                    # stdio mode (MCP client)
    python mcp-server.py http               # HTTP API mode
    python mcp-server.py dev                # Development mode with hot-reload
    python mcp-server.py stdio --debug      # stdio mode with debug logging
    python mcp-server.py http --port 8080   # HTTP mode on port 8080
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def log(message: str, level: str = "INFO") -> None:
    """Log a message with color coding."""
    colors = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "DEBUG": Colors.MAGENTA
    }
    color = colors.get(level, Colors.END)
    print(f"{color}[{level}]{Colors.END} {message}")


def run_stdio_mode(args: argparse.Namespace) -> None:
    """Run server in stdio mode for MCP client integration."""
    # In stdio mode, suppress all output to avoid breaking JSON communication
    # Only log to stderr if debug is enabled
    if args.debug:
        log("Starting MCP Jive Server in stdio mode", "INFO")
        log("Mode: stdio (MCP client integration)", "INFO")
    
    # Set environment variables for stdio mode
    env = os.environ.copy()
    env["MCP_JIVE_ENV"] = "development" if args.debug else "production"
    env["MCP_JIVE_DEBUG"] = "true" if args.debug else "false"
    
    if args.log_level:
        env["MCP_JIVE_LOG_LEVEL"] = args.log_level
    elif args.debug:
        env["MCP_JIVE_LOG_LEVEL"] = "DEBUG"
    
    # Build command with absolute path
    main_py_path = project_root / "src" / "main.py"
    cmd = [sys.executable, str(main_py_path), "--stdio"]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        if args.debug:
            log("Server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        if args.debug:
            log(f"Server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


def run_http_mode(args: argparse.Namespace) -> None:
    """Run server in HTTP mode for web API access."""
    log("Starting MCP Jive Server in HTTP mode", "INFO")
    log(f"Mode: HTTP API (http://{args.host or 'localhost'}:{args.port or 3456})", "INFO")
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_JIVE_ENV"] = "development" if args.debug else "production"
    env["MCP_JIVE_DEBUG"] = "true" if args.debug else "false"
    
    if args.log_level:
        env["MCP_JIVE_LOG_LEVEL"] = args.log_level
    elif args.debug:
        env["MCP_JIVE_LOG_LEVEL"] = "DEBUG"
    
    # Build command with absolute path
    main_py_path = project_root / "src" / "main.py"
    cmd = [sys.executable, str(main_py_path), "--http"]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        log("Server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        log(f"Server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


def run_websocket_mode(args: argparse.Namespace) -> None:
    """Run server in WebSocket mode for real-time communication."""
    log("Starting MCP Jive Server in WebSocket mode", "INFO")
    log(f"Mode: WebSocket (ws://{args.host or 'localhost'}:{args.port or 3456})", "INFO")
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_JIVE_ENV"] = "development" if args.debug else "production"
    env["MCP_JIVE_DEBUG"] = "true" if args.debug else "false"
    
    if args.log_level:
        env["MCP_JIVE_LOG_LEVEL"] = args.log_level
    elif args.debug:
        env["MCP_JIVE_LOG_LEVEL"] = "DEBUG"
    
    # Build command with absolute path
    main_py_path = project_root / "src" / "main.py"
    cmd = [sys.executable, str(main_py_path), "--websocket"]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        log("Server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        log(f"Server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


def run_dev_mode(args: argparse.Namespace) -> None:
    """Run server in development mode with hot-reload."""
    log("Starting MCP Jive Server in development mode", "INFO")
    log("Mode: Development (hot-reload enabled)", "INFO")
    
    # Build command for dev-server.py with absolute path
    dev_server_path = project_root / "scripts" / "dev-server.py"
    cmd = [sys.executable, str(dev_server_path)]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    if args.no_reload:
        cmd.append("--no-reload")
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        log("Development server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        log(f"Development server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified MCP Jive Server Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  stdio       Run in stdio mode for MCP client integration (default)
  http        Run in HTTP mode for web API access
  websocket   Run in WebSocket mode for real-time communication
  dev         Run in development mode with hot-reload

Examples:
  %(prog)s                    # stdio mode (MCP client)
  %(prog)s http               # HTTP API mode
  %(prog)s dev                # Development mode with hot-reload
  %(prog)s stdio --debug      # stdio mode with debug logging
  %(prog)s http --port 8080   # HTTP mode on port 8080

Environment Variables:
  MCP_JIVE_HOST              # Server host (default: localhost)
  MCP_JIVE_PORT              # Server port (default: 3456)
  MCP_JIVE_LOG_LEVEL         # Log level (default: INFO)
  MCP_JIVE_DEBUG             # Debug mode (default: false)
"""
    )
    
    # Mode argument (positional, optional)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["stdio", "http", "websocket", "dev"],
        default="stdio",
        help="Server mode (default: stdio)"
    )
    
    # Server options
    parser.add_argument(
        "--host",
        type=str,
        help="Server host address (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Server port number (default: 3456)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (.env format)"
    )
    
    # Development mode options
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload in dev mode"
    )
    
    return parser.parse_args()


def print_startup_banner(mode: str, args: argparse.Namespace) -> None:
    """Print startup banner with configuration info."""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                     MCP Jive Server                         ║")
    print("║                  Unified Entry Point                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"  Mode: {Colors.GREEN}{mode.upper()}{Colors.END}")
    print(f"  Host: {args.host or 'localhost'}")
    print(f"  Port: {args.port or 3456}")
    print(f"  Debug: {Colors.YELLOW if args.debug else Colors.DIM}{args.debug}{Colors.END}")
    print(f"  Log Level: {args.log_level or 'INFO'}")
    if args.config:
        print(f"  Config: {args.config}")
    print()


def main() -> None:
    """Main entry point."""
    try:
        args = parse_arguments()
        
        # Print startup banner (suppress in stdio mode to avoid breaking JSON)
        if args.mode != "stdio":
            print_startup_banner(args.mode, args)
        
        # Route to appropriate mode handler
        if args.mode == "stdio":
            run_stdio_mode(args)
        elif args.mode == "http":
            run_http_mode(args)
        elif args.mode == "websocket":
            run_websocket_mode(args)
        elif args.mode == "dev":
            run_dev_mode(args)
        else:
            log(f"Unknown mode: {args.mode}", "ERROR")
            sys.exit(1)
            
    except KeyboardInterrupt:
        log("Server startup cancelled by user", "INFO")
        sys.exit(0)
    except Exception as e:
        log(f"Failed to start server: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()