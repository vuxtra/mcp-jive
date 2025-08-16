#!/usr/bin/env python3
"""
MCP Jive Development Server

A development server with hot-reload, enhanced logging, and development features.
This server automatically restarts when code changes are detected.

Usage:
    ./bin/mcp-jive server dev [options]

Options:
    --host HOST         Server host (default: localhost)
    --port PORT         Server port (default: 3456)
    --reload-dirs DIRS  Additional directories to watch (comma-separated)
    --no-reload         Disable auto-reload
    --log-level LEVEL   Log level (DEBUG, INFO, WARNING, ERROR)
    --config FILE       Configuration file path
    --help              Show this help message
"""

import argparse
import asyncio
import os
import sys
import signal
import time
from pathlib import Path
from typing import List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
import threading
import subprocess
import logging
from datetime import datetime

# Add src to Python path
project_root = Path(__file__).parent.parent.parent
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


class DevLogger:
    """Enhanced logger for development server."""
    
    def __init__(self, level: str = "INFO"):
        self.level = getattr(logging, level.upper())
        self.setup_logging()
        
    def setup_logging(self):
        """Setup enhanced logging for development."""
        # Create custom formatter
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': Colors.DIM,
                'INFO': Colors.BLUE,
                'WARNING': Colors.YELLOW,
                'ERROR': Colors.RED,
                'CRITICAL': Colors.RED + Colors.BOLD
            }
            
            def format(self, record):
                # Add timestamp
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Color the level name
                level_color = self.COLORS.get(record.levelname, '')
                colored_level = f"{level_color}[{record.levelname}]{Colors.END}"
                
                # Format the message
                message = super().format(record)
                return f"{Colors.DIM}{timestamp}{Colors.END} {colored_level} {message}"
        
        # Setup root logger
        logging.basicConfig(
            level=self.level,
            format='%(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Apply colored formatter
        for handler in logging.root.handlers:
            handler.setFormatter(ColoredFormatter())
            
    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        logger = logging.getLogger("dev-server")
        getattr(logger, level.lower())(message)


class CodeChangeHandler(FileSystemEventHandler):
    """Handle file system events for hot-reload."""
    
    def __init__(self, server_manager, logger: DevLogger):
        self.server_manager = server_manager
        self.logger = logger
        self.last_reload = 0
        self.reload_delay = 1.0  # Minimum delay between reloads
        self.ignored_extensions = {'.pyc', '.pyo', '.pyd', '__pycache__'}
        self.ignored_dirs = {'__pycache__', '.git', '.pytest_cache', 'venv', 'node_modules'}
        
    def should_reload(self, file_path: str) -> bool:
        """Check if file change should trigger reload."""
        path = Path(file_path)
        
        # Ignore certain file extensions
        if path.suffix in self.ignored_extensions:
            return False
            
        # Ignore certain directories
        if any(ignored in path.parts for ignored in self.ignored_dirs):
            return False
            
        # Only reload for Python files and config files
        if path.suffix not in {'.py', '.yaml', '.yml', '.json', '.toml', '.env'}:
            return False
            
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_reload < self.reload_delay:
            return False
            
        return True
        
    def on_modified(self, event):
        """Handle file modification events."""
        if not isinstance(event, (FileModifiedEvent, FileCreatedEvent)):
            return
            
        if event.is_directory:
            return
            
        if self.should_reload(event.src_path):
            self.last_reload = time.time()
            relative_path = Path(event.src_path).relative_to(project_root)
            self.logger.log(f"File changed: {relative_path}", "INFO")
            self.server_manager.restart_server()
            
    def on_created(self, event):
        """Handle file creation events."""
        self.on_modified(event)


class ServerManager:
    """Manage the MCP server process with hot-reload capability."""
    
    def __init__(self, args, logger: DevLogger):
        self.args = args
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.restart_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def start_server(self):
        """Start the MCP server process."""
        with self.lock:
            if self.process and self.process.poll() is None:
                self.logger.log("Server is already running", "WARNING")
                return
                
            self.logger.log("Starting MCP Jive server...", "INFO")
            
            # Prepare environment
            env = os.environ.copy()
            env['MCP_ENV'] = 'development'
            env['MCP_DEV_MODE'] = 'true'
            env['MCP_LOG_LEVEL'] = self.args.log_level
            env['MCP_AUTO_RELOAD'] = 'false'  # We handle reload ourselves
            env['PYTHONPATH'] = str(project_root / "src")
            
            # Load development environment file
            env_file = project_root / ".env.dev"
            if env_file.exists():
                self.load_env_file(env_file, env)
                
            # Override with command line arguments
            env['MCP_SERVER_HOST'] = self.args.host
            env['MCP_SERVER_PORT'] = str(self.args.port)
            
            try:
                # Start the server process
                cmd = [
                    sys.executable,
                    "main.py",
                    "--http",  # Enable HTTP mode
                    "--host", self.args.host,
                    "--port", str(self.args.port),
                    "--log-level", self.args.log_level
                ]
                
                if self.args.config:
                    cmd.extend(["--config", self.args.config])
                    
                self.process = subprocess.Popen(
                    cmd,
                    cwd=project_root / "src",
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                self.restart_count += 1
                uptime = time.time() - self.start_time
                
                self.logger.log(
                    f"Server started (PID: {self.process.pid}, Restart #{self.restart_count}, Uptime: {uptime:.1f}s)",
                    "INFO"
                )
                
                # Start output monitoring in a separate thread
                threading.Thread(
                    target=self.monitor_output,
                    daemon=True
                ).start()
                
            except Exception as e:
                self.logger.log(f"Failed to start server: {e}", "ERROR")
                
    def load_env_file(self, env_file: Path, env: dict):
        """Load environment variables from file."""
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env[key.strip()] = value.strip()
        except Exception as e:
            self.logger.log(f"Failed to load {env_file}: {e}", "WARNING")
            
    def monitor_output(self):
        """Monitor server output and log it."""
        if not self.process or not self.process.stdout:
            return
            
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    # Parse and colorize server output
                    line = line.rstrip()
                    if line:
                        self.format_server_output(line)
                        
        except Exception as e:
            self.logger.log(f"Output monitoring error: {e}", "ERROR")
            
    def format_server_output(self, line: str):
        """Format and colorize server output."""
        # Simple log level detection and coloring
        line_lower = line.lower()
        
        if 'error' in line_lower or 'exception' in line_lower:
            color = Colors.RED
        elif 'warning' in line_lower or 'warn' in line_lower:
            color = Colors.YELLOW
        elif 'info' in line_lower:
            color = Colors.BLUE
        elif 'debug' in line_lower:
            color = Colors.DIM
        else:
            color = ''
            
        # Add server prefix
        prefix = f"{Colors.MAGENTA}[SERVER]{Colors.END}"
        print(f"{prefix} {color}{line}{Colors.END}")
        
    def stop_server(self):
        """Stop the MCP server process."""
        with self.lock:
            if self.process and self.process.poll() is None:
                self.logger.log("Stopping server...", "INFO")
                
                try:
                    # Try graceful shutdown first
                    self.process.terminate()
                    
                    # Wait for graceful shutdown with longer timeout
                    try:
                        self.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        self.logger.log("Graceful shutdown timed out, force killing server...", "WARNING")
                        self.process.kill()
                        self.process.wait()
                        
                    self.logger.log("Server stopped", "INFO")
                    
                except Exception as e:
                    self.logger.log(f"Error stopping server: {e}", "ERROR")
                    
                self.process = None
                
    def restart_server(self):
        """Restart the MCP server."""
        self.logger.log(f"{Colors.CYAN}🔄 Restarting server...{Colors.END}", "INFO")
        self.stop_server()
        time.sleep(0.5)  # Brief pause
        self.start_server()
        
    def is_running(self) -> bool:
        """Check if server is running."""
        return self.process is not None and self.process.poll() is None


class DevServer:
    """Main development server class."""
    
    def __init__(self, args):
        self.args = args
        self.logger = DevLogger(args.log_level)
        self.server_manager = ServerManager(args, self.logger)
        self.observer: Optional[Observer] = None
        self.running = False
        
    def setup_file_watcher(self):
        """Setup file system watcher for hot-reload."""
        if self.args.no_reload:
            self.logger.log("Hot-reload disabled", "INFO")
            return
            
        self.logger.log("Setting up file watcher...", "INFO")
        
        # Create event handler
        handler = CodeChangeHandler(self.server_manager, self.logger)
        
        # Setup observer
        self.observer = Observer()
        
        # Watch source directory
        src_dir = project_root / "src"
        if src_dir.exists():
            self.observer.schedule(handler, str(src_dir), recursive=True)
            self.logger.log(f"Watching: {src_dir}", "DEBUG")
            
        # Watch additional directories
        if self.args.reload_dirs:
            for dir_path in self.args.reload_dirs.split(','):
                dir_path = Path(dir_path.strip())
                if dir_path.exists():
                    self.observer.schedule(handler, str(dir_path), recursive=True)
                    self.logger.log(f"Watching: {dir_path}", "DEBUG")
                    
        # Watch configuration files
        config_files = ['.env.dev', 'pyproject.toml', 'setup.py']
        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                self.observer.schedule(handler, str(config_path.parent), recursive=False)
                
        self.observer.start()
        self.logger.log("File watcher started", "INFO")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.log("\nReceived shutdown signal", "INFO")
            self.shutdown()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def print_startup_info(self):
        """Print startup information."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}🚀 MCP Jive Development Server{Colors.END}\n")
        
        print(f"{Colors.BOLD}Configuration:{Colors.END}")
        print(f"  Host: {Colors.CYAN}{self.args.host}{Colors.END}")
        print(f"  Port: {Colors.CYAN}{self.args.port}{Colors.END}")
        print(f"  Log Level: {Colors.CYAN}{self.args.log_level}{Colors.END}")
        print(f"  Hot Reload: {Colors.CYAN}{'Enabled' if not self.args.no_reload else 'Disabled'}{Colors.END}")
        
        if self.args.config:
            print(f"  Config File: {Colors.CYAN}{self.args.config}{Colors.END}")
            
        print(f"\n{Colors.BOLD}URLs:{Colors.END}")
        print(f"  Server: {Colors.BLUE}http://{self.args.host}:{self.args.port}{Colors.END}")
        print(f"  Health: {Colors.BLUE}http://{self.args.host}:{self.args.port}/health{Colors.END}")
        print(f"  Metrics: {Colors.BLUE}http://{self.args.host}:{self.args.port}/metrics{Colors.END}")
        
        print(f"\n{Colors.BOLD}Commands:{Colors.END}")
        print(f"  {Colors.DIM}Ctrl+C{Colors.END} - Shutdown server")
        print(f"  {Colors.DIM}Ctrl+R{Colors.END} - Manual restart (if supported)")
        print()
        
    def run(self):
        """Run the development server."""
        try:
            self.running = True
            
            # Print startup info
            self.print_startup_info()
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Setup file watcher
            self.setup_file_watcher()
            
            # Start the server
            self.server_manager.start_server()
            
            # Keep the main thread alive
            self.logger.log("Development server is running. Press Ctrl+C to stop.", "INFO")
            
            while self.running:
                time.sleep(1)
                
                # Check if server process died unexpectedly
                if not self.server_manager.is_running():
                    self.logger.log("Server process died unexpectedly", "ERROR")
                    if self.running:  # Only restart if we're still supposed to be running
                        self.logger.log("Attempting to restart...", "INFO")
                        time.sleep(2)
                        self.server_manager.start_server()
                        
        except KeyboardInterrupt:
            self.logger.log("\nShutdown requested", "INFO")
        except Exception as e:
            self.logger.log(f"Development server error: {e}", "ERROR")
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Shutdown the development server."""
        if not self.running:
            return
            
        self.running = False
        self.logger.log("Shutting down development server...", "INFO")
        
        # Stop file watcher
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        # Stop server
        self.server_manager.stop_server()
        
        self.logger.log("Development server stopped", "INFO")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Jive Development Server with hot-reload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./bin/mcp-jive server dev                           # Start with defaults
  ./bin/mcp-jive server dev --port 8080               # Custom port
  ./bin/mcp-jive server dev --no-reload               # Disable hot-reload
  ./bin/mcp-jive server dev --log-level DEBUG         # Debug logging
  ./bin/mcp-jive server dev --reload-dirs tests,docs  # Watch additional dirs
"""
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3456,
        help="Server port (default: 3456)"
    )
    parser.add_argument(
        "--reload-dirs",
        help="Additional directories to watch (comma-separated)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--config",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"{Colors.YELLOW}Warning: Not running in a virtual environment{Colors.END}")
        print(f"Consider running: {Colors.BLUE}source venv/bin/activate{Colors.END}\n")
        
    # Start development server
    dev_server = DevServer(args)
    dev_server.run()


if __name__ == "__main__":
    main()