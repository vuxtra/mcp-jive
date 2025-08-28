#!/usr/bin/env python3
"""Unified MCP Jive Server Entry Point.

This is the single, unified entry point for the MCP Jive server that replaces
all the scattered startup scripts with a clean, flag-based interface.

Usage:
    ./bin/mcp-jive server [mode] [options]

Modes:
    stdio       Run in stdio mode for MCP client integration
    http        Run in HTTP mode for web API access
    combined    Run in combined mode (HTTP + WebSocket) (default)
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
    ./bin/mcp-jive server start --mode stdio             # stdio mode (MCP client)
    ./bin/mcp-jive server http              # HTTP API mode
    ./bin/mcp-jive server combined          # Combined HTTP + WebSocket mode
    ./bin/mcp-jive server dev               # Development mode with hot-reload
    ./bin/mcp-jive server start --mode stdio --debug     # stdio mode with debug logging
    ./bin/mcp-jive server http --port 8080  # HTTP mode on port 8080
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


def log(message: str, level: str = "INFO", stdio_mode: bool = False) -> None:
    """Log a message with color coding."""
    if stdio_mode:
        # In stdio mode, only log to stderr without colors to avoid breaking JSON-RPC
        import sys
        print(f"[{level}] {message}", file=sys.stderr)
    else:
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
        log("Starting MCP Jive Server in stdio mode", "INFO", stdio_mode=True)
        log("Mode: stdio (MCP client integration)", "INFO", stdio_mode=True)
    
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
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
    
    # Execute with proper working directory
    try:
        # In stdio mode, redirect only stdout/stderr to prevent output pollution
        # but keep stdin open for MCP communication
        if args.debug:
            subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
        else:
            # Redirect only stdout and stderr to DEVNULL to prevent output pollution
            # Keep stdin open for MCP JSON-RPC communication
            subprocess.run(cmd, env=env, check=True, cwd=str(project_root), 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except KeyboardInterrupt:
        if args.debug:
            log("Server stopped by user", "INFO", stdio_mode=True)
    except subprocess.CalledProcessError as e:
        if args.debug:
            log(f"Server failed with exit code {e.returncode}", "ERROR", stdio_mode=True)
        sys.exit(e.returncode)


def run_http_mode(args: argparse.Namespace) -> None:
    """Run server in HTTP mode for web API access."""
    log("Starting MCP Jive Server in HTTP mode", "INFO")
    log(f"Mode: HTTP API (http://{args.host or 'localhost'}:{args.port or 3454})", "INFO")
    
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
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        log("HTTP server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        log(f"HTTP server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


# WebSocket mode has been consolidated into combined mode
# Use run_combined_mode() instead


def run_dev_mode(args: argparse.Namespace) -> None:
    """Run server in development mode with hot-reload."""
    log("Starting MCP Jive Server in development mode", "INFO")
    log("Mode: Development (hot-reload enabled)", "INFO")
    
    # Set environment variables
    env = os.environ.copy()
    env["MCP_JIVE_ENV"] = "development"
    env["MCP_JIVE_DEBUG"] = "true" if args.debug else "false"
    
    if args.log_level:
        env["MCP_JIVE_LOG_LEVEL"] = args.log_level
    elif args.debug:
        env["MCP_JIVE_LOG_LEVEL"] = "DEBUG"
    
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
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
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


def run_combined_mode(args: argparse.Namespace) -> None:
    """Run server in combined mode (stdio + http + websocket)."""
    log("Starting MCP Jive Server in combined mode", "INFO")
    log("Mode: Combined (stdio + HTTP + WebSocket)", "INFO")
    
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
    cmd = [sys.executable, str(main_py_path), "--combined"]
    
    if args.host:
        cmd.extend(["--host", args.host])
    if args.port:
        cmd.extend(["--port", str(args.port)])
    if args.config:
        cmd.extend(["--config", args.config])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
    
    # Execute with proper working directory
    try:
        subprocess.run(cmd, env=env, check=True, cwd=str(project_root))
    except KeyboardInterrupt:
        log("Combined server stopped by user", "INFO")
    except subprocess.CalledProcessError as e:
        log(f"Combined server failed with exit code {e.returncode}", "ERROR")
        sys.exit(e.returncode)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified MCP Jive Server Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  stdio       Run in stdio mode for MCP client integration
  http        Run in HTTP mode for web API access
  combined    Run in combined mode (HTTP + WebSocket) (default)
  dev         Run in development mode with hot-reload

Examples:
  %(prog)s                    # combined mode (default)
  %(prog)s stdio              # stdio mode (MCP client)
  %(prog)s http               # HTTP API mode
  %(prog)s dev                # Development mode with hot-reload
  %(prog)s stdio --debug      # stdio mode with debug logging
  %(prog)s http --port 8080   # HTTP mode on port 8080

Environment Variables:
  MCP_JIVE_HOST              # Server host (default: localhost)
  MCP_JIVE_PORT              # Server port (default: 3454)
  MCP_JIVE_LOG_LEVEL         # Log level (default: INFO)
  MCP_JIVE_DEBUG             # Debug mode (default: false)
"""
    )
    
    # Mode argument (positional, optional)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["stdio", "http", "websocket", "dev", "combined"],
        default="combined",
        help="Server mode (default: combined)"
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
        help="Server port number (default: 3454)"
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
    
    # Database options
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to LanceDB database directory"
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
    print(f"  Port: {args.port or 3454}")
    print(f"  Debug: {Colors.YELLOW if args.debug else Colors.DIM}{args.debug}{Colors.END}")
    print(f"  Log Level: {args.log_level or 'INFO'}")
    if args.config:
        print(f"  Config: {args.config}")
    print()


def main() -> None:
    """Main entry point."""
    stdio_mode = False  # Default value
    try:
        args = parse_arguments()
        stdio_mode = (args.mode == "stdio")
        
        # Print startup banner (suppress in stdio mode to avoid breaking JSON)
        if args.mode != "stdio":
            print_startup_banner(args.mode, args)
        
        # Route to appropriate mode handler
        if args.mode == "stdio":
            run_stdio_mode(args)
        elif args.mode == "http":
            run_http_mode(args)
        elif args.mode == "websocket":
            # WebSocket mode has been consolidated into combined mode
            log("WebSocket mode is now part of combined mode. Using combined mode instead.", "INFO", stdio_mode)
            run_combined_mode(args)
        elif args.mode == "dev":
            run_dev_mode(args)
        elif args.mode == "combined":
            run_combined_mode(args)
        else:
            log(f"Unknown mode: {args.mode}", "ERROR", stdio_mode)
            sys.exit(1)
            
    except KeyboardInterrupt:
        log("Server startup cancelled by user", "INFO", stdio_mode)
        sys.exit(0)
    except Exception as e:
        log(f"Failed to start server: {e}", "ERROR", stdio_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()