#!/usr/bin/env python3
"""
MCP Jive Development CLI

Provides convenient commands for development tasks including testing,
code quality checks, server management, and more.

Usage:
    python scripts/dev.py <command> [options]

Commands:
    test            Run tests
    test-unit       Run unit tests only
    test-integration Run integration tests only
    test-mcp        Run MCP protocol tests only
    test-coverage   Run tests with coverage report
    lint            Run code linting
    format          Format code with black and isort
    type-check      Run type checking with mypy
    security        Run security checks
    quality         Run all quality checks (lint + type-check + security)
    start           Start development server
    start-prod      Start production server
    health          Check server health
    clean           Clean build artifacts and cache
    deps            Install/update dependencies
    docs            Generate documentation
    db-reset        Reset development database
    logs            Show server logs
    shell           Start interactive Python shell
    version         Show version information
"""

import sys
import subprocess
import argparse
import os
import shutil
from pathlib import Path
from typing import List, Optional
import json
import time

# Project paths
project_root = Path(__file__).parent.parent
venv_python = project_root / "venv" / "bin" / "python"
venv_pip = project_root / "venv" / "bin" / "pip"

# Check if we're on Windows
if os.name == 'nt':
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    venv_pip = project_root / "venv" / "Scripts" / "pip.exe"


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


class DevCLI:
    """Development CLI class."""
    
    def __init__(self):
        self.project_root = project_root
        self.venv_python = str(venv_python)
        self.venv_pip = str(venv_pip)
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with color coding."""
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "HEADER": Colors.BOLD + Colors.CYAN
        }
        color = colors.get(level, Colors.BLUE)
        print(f"{color}[{level}]{Colors.END} {message}")
        
    def run_cmd(self, cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            self.log(f"Running: {' '.join(cmd)}", "INFO")
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                check=check,
                capture_output=False,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed with exit code {e.returncode}", "ERROR")
            sys.exit(e.returncode)
            
    def check_venv(self):
        """Check if virtual environment exists and is activated."""
        if not Path(self.venv_python).exists():
            self.log("Virtual environment not found. Run setup-dev.py first.", "ERROR")
            sys.exit(1)
            
        # Check if we're in the virtual environment
        if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
            self.log("Virtual environment not activated. Consider running:", "WARNING")
            if os.name == 'nt':
                self.log(f"  {Colors.CYAN}venv\\Scripts\\activate{Colors.END}", "WARNING")
            else:
                self.log(f"  {Colors.CYAN}source venv/bin/activate{Colors.END}", "WARNING")
            print()
    
    def test(self, args):
        """Run tests."""
        self.log("Running all tests...", "HEADER")
        
        cmd = [self.venv_python, "-m", "pytest"]
        
        # Add test directory
        cmd.append("tests/")
        
        # Add additional arguments
        if args.verbose:
            cmd.append("-v")
        if args.parallel:
            cmd.extend(["-n", "auto"])
        if args.failfast:
            cmd.append("-x")
        if args.pattern:
            cmd.extend(["-k", args.pattern])
            
        self.run_cmd(cmd)
        self.log("Tests completed successfully!", "SUCCESS")
    
    def test_unit(self, args):
        """Run unit tests only."""
        self.log("Running unit tests...", "HEADER")
        
        cmd = [self.venv_python, "-m", "pytest", "tests/unit/", "-m", "unit"]
        
        if args.verbose:
            cmd.append("-v")
        if args.parallel:
            cmd.extend(["-n", "auto"])
            
        self.run_cmd(cmd)
        self.log("Unit tests completed successfully!", "SUCCESS")
    
    def test_integration(self, args):
        """Run integration tests only."""
        self.log("Running integration tests...", "HEADER")
        
        cmd = [self.venv_python, "-m", "pytest", "tests/integration/", "-m", "integration"]
        
        if args.verbose:
            cmd.append("-v")
            
        self.run_cmd(cmd)
        self.log("Integration tests completed successfully!", "SUCCESS")
    
    def test_mcp(self, args):
        """Run MCP protocol tests only."""
        self.log("Running MCP protocol tests...", "HEADER")
        
        cmd = [self.venv_python, "-m", "pytest", "tests/mcp/", "-m", "mcp"]
        
        if args.verbose:
            cmd.append("-v")
            
        self.run_cmd(cmd)
        self.log("MCP tests completed successfully!", "SUCCESS")
    
    def test_coverage(self, args):
        """Run tests with coverage report."""
        self.log("Running tests with coverage...", "HEADER")
        
        cmd = [
            self.venv_python, "-m", "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80",
            "tests/"
        ]
        
        if args.verbose:
            cmd.append("-v")
            
        self.run_cmd(cmd)
        
        # Open coverage report if requested
        if args.open:
            coverage_file = self.project_root / "htmlcov" / "index.html"
            if coverage_file.exists():
                import webbrowser
                webbrowser.open(f"file://{coverage_file}")
                
        self.log("Coverage report generated successfully!", "SUCCESS")
    
    def lint(self, args):
        """Run code linting."""
        self.log("Running code linting...", "HEADER")
        
        # Run flake8
        self.log("Running flake8...", "INFO")
        self.run_cmd([self.venv_python, "-m", "flake8", "src/", "tests/", "scripts/"])
        
        # Run bandit for security
        self.log("Running bandit security check...", "INFO")
        self.run_cmd([self.venv_python, "-m", "bandit", "-r", "src/"])
        
        self.log("Linting completed successfully!", "SUCCESS")
    
    def format_code(self, args):
        """Format code with black and isort."""
        self.log("Formatting code...", "HEADER")
        
        # Run black
        self.log("Running black formatter...", "INFO")
        black_cmd = [self.venv_python, "-m", "black", "src/", "tests/", "scripts/"]
        if args.check:
            black_cmd.append("--check")
        if args.diff:
            black_cmd.append("--diff")
        self.run_cmd(black_cmd)
        
        # Run isort
        self.log("Running isort import sorter...", "INFO")
        isort_cmd = [self.venv_python, "-m", "isort", "src/", "tests/", "scripts/"]
        if args.check:
            isort_cmd.append("--check-only")
        if args.diff:
            isort_cmd.append("--diff")
        self.run_cmd(isort_cmd)
        
        self.log("Code formatting completed successfully!", "SUCCESS")
    
    def type_check(self, args):
        """Run type checking with mypy."""
        self.log("Running type checking...", "HEADER")
        
        cmd = [self.venv_python, "-m", "mypy", "src/"]
        
        if args.strict:
            cmd.append("--strict")
            
        self.run_cmd(cmd)
        self.log("Type checking completed successfully!", "SUCCESS")
    
    def security(self, args):
        """Run security checks."""
        self.log("Running security checks...", "HEADER")
        
        # Run bandit
        self.log("Running bandit...", "INFO")
        self.run_cmd([self.venv_python, "-m", "bandit", "-r", "src/"])
        
        # Run safety
        self.log("Running safety check...", "INFO")
        self.run_cmd([self.venv_python, "-m", "safety", "check"])
        
        self.log("Security checks completed successfully!", "SUCCESS")
    
    def quality(self, args):
        """Run all quality checks."""
        self.log("Running all quality checks...", "HEADER")
        
        # Run linting
        self.lint(args)
        
        # Run type checking
        self.type_check(args)
        
        # Run security checks
        self.security(args)
        
        self.log("All quality checks completed successfully!", "SUCCESS")
    
    def start(self, args):
        """Start development server."""
        self.log("Starting development server...", "HEADER")
        
        cmd = [self.venv_python, "scripts/dev-server.py"]
        
        if args.host:
            cmd.extend(["--host", args.host])
        if args.port:
            cmd.extend(["--port", str(args.port)])
        if args.no_reload:
            cmd.append("--no-reload")
        if args.log_level:
            cmd.extend(["--log-level", args.log_level])
            
        self.run_cmd(cmd)
    
    def start_prod(self, args):
        """Start production server."""
        self.log("Starting production server...", "HEADER")
        
        cmd = [self.venv_python, "-m", "mcp_server.main"]
        
        if args.host:
            cmd.extend(["--host", args.host])
        if args.port:
            cmd.extend(["--port", str(args.port)])
        if args.config:
            cmd.extend(["--config", args.config])
            
        self.run_cmd(cmd)
    
    def health(self, args):
        """Check server health."""
        self.log("Checking server health...", "HEADER")
        
        import requests
        
        host = args.host or "localhost"
        port = args.port or 3456
        
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"Server is healthy: {health_data}", "SUCCESS")
            else:
                self.log(f"Server health check failed: {response.status_code}", "ERROR")
        except requests.RequestException as e:
            self.log(f"Failed to connect to server: {e}", "ERROR")
    
    def clean(self, args):
        """Clean build artifacts and cache."""
        self.log("Cleaning build artifacts...", "HEADER")
        
        # Directories to clean
        clean_dirs = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "htmlcov",
            "dist",
            "build",
            "*.egg-info"
        ]
        
        # Files to clean
        clean_files = [
            "coverage.xml",
            ".coverage"
        ]
        
        for pattern in clean_dirs:
            for path in self.project_root.rglob(pattern):
                if path.is_dir():
                    self.log(f"Removing directory: {path}", "INFO")
                    shutil.rmtree(path, ignore_errors=True)
                    
        for pattern in clean_files:
            for path in self.project_root.rglob(pattern):
                if path.is_file():
                    self.log(f"Removing file: {path}", "INFO")
                    path.unlink(missing_ok=True)
                    
        self.log("Cleanup completed successfully!", "SUCCESS")
    
    def deps(self, args):
        """Install/update dependencies."""
        self.log("Managing dependencies...", "HEADER")
        
        if args.update:
            self.log("Updating dependencies...", "INFO")
            self.run_cmd([self.venv_pip, "install", "--upgrade", "-r", "requirements.txt"])
        else:
            self.log("Installing dependencies...", "INFO")
            self.run_cmd([self.venv_pip, "install", "-r", "requirements.txt"])
            
        # Install development dependencies
        if args.dev:
            self.log("Installing development dependencies...", "INFO")
            self.run_cmd([self.venv_pip, "install", "-e", ".[dev]"])
            
        self.log("Dependencies managed successfully!", "SUCCESS")
    
    def docs(self, args):
        """Generate documentation."""
        self.log("Generating documentation...", "HEADER")
        
        # This would generate documentation when implemented
        # For now, just show what would be done
        self.log("Documentation generation not yet implemented", "WARNING")
        self.log("Would generate API docs, user guides, etc.", "INFO")
    
    def db_reset(self, args):
        """Reset development database."""
        self.log("Resetting development database...", "HEADER")
        
        # Remove Weaviate data directory if it exists
        data_dir = self.project_root / "data"
        if data_dir.exists():
            self.log(f"Removing data directory: {data_dir}", "INFO")
            shutil.rmtree(data_dir, ignore_errors=True)
            
        self.log("Database reset completed!", "SUCCESS")
    
    def logs(self, args):
        """Show server logs."""
        self.log("Showing server logs...", "HEADER")
        
        log_file = self.project_root / "logs" / "mcp-jive.log"
        if log_file.exists():
            if args.follow:
                # Follow logs (tail -f equivalent)
                self.run_cmd(["tail", "-f", str(log_file)])
            else:
                # Show last N lines
                lines = args.lines or 50
                self.run_cmd(["tail", "-n", str(lines), str(log_file)])
        else:
            self.log("Log file not found", "WARNING")
    
    def shell(self, args):
        """Start interactive Python shell."""
        self.log("Starting interactive Python shell...", "HEADER")
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root / "src")
        
        # Start IPython if available, otherwise regular Python
        try:
            self.run_cmd([self.venv_python, "-c", "import IPython; IPython.start_ipython()"])
        except subprocess.CalledProcessError:
            self.log("IPython not available, starting regular Python shell", "INFO")
            self.run_cmd([self.venv_python, "-i", "-c", "import sys; sys.path.insert(0, 'src')"])
    
    def version(self, args):
        """Show version information."""
        self.log("Version Information", "HEADER")
        
        # Show Python version
        result = subprocess.run([self.venv_python, "--version"], capture_output=True, text=True)
        self.log(f"Python: {result.stdout.strip()}", "INFO")
        
        # Show package version
        try:
            result = subprocess.run(
                [self.venv_python, "-c", "import mcp_server; print(mcp_server.__version__)"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                self.log(f"MCP Jive: {result.stdout.strip()}", "INFO")
            else:
                self.log("MCP Jive: Not installed", "WARNING")
        except:
            self.log("MCP Jive: Not installed", "WARNING")
        
        # Show key dependencies
        deps = ["pytest", "black", "mypy", "flake8", "fastapi", "weaviate-client"]
        for dep in deps:
            try:
                result = subprocess.run(
                    [self.venv_python, "-c", f"import {dep.replace('-', '_')}; print({dep.replace('-', '_')}.__version__)"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    self.log(f"{dep}: {result.stdout.strip()}", "INFO")
            except:
                pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Jive Development CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test commands
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("-p", "--parallel", action="store_true", help="Run tests in parallel")
    test_parser.add_argument("-x", "--failfast", action="store_true", help="Stop on first failure")
    test_parser.add_argument("-k", "--pattern", help="Run tests matching pattern")
    
    test_unit_parser = subparsers.add_parser("test-unit", help="Run unit tests only")
    test_unit_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_unit_parser.add_argument("-p", "--parallel", action="store_true", help="Run tests in parallel")
    
    test_integration_parser = subparsers.add_parser("test-integration", help="Run integration tests only")
    test_integration_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    test_mcp_parser = subparsers.add_parser("test-mcp", help="Run MCP protocol tests only")
    test_mcp_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    test_coverage_parser = subparsers.add_parser("test-coverage", help="Run tests with coverage")
    test_coverage_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    test_coverage_parser.add_argument("--open", action="store_true", help="Open coverage report in browser")
    
    # Code quality commands
    lint_parser = subparsers.add_parser("lint", help="Run code linting")
    
    format_parser = subparsers.add_parser("format", help="Format code")
    format_parser.add_argument("--check", action="store_true", help="Check formatting without making changes")
    format_parser.add_argument("--diff", action="store_true", help="Show diff of changes")
    
    type_check_parser = subparsers.add_parser("type-check", help="Run type checking")
    type_check_parser.add_argument("--strict", action="store_true", help="Use strict type checking")
    
    security_parser = subparsers.add_parser("security", help="Run security checks")
    quality_parser = subparsers.add_parser("quality", help="Run all quality checks")
    
    # Server commands
    start_parser = subparsers.add_parser("start", help="Start development server")
    start_parser.add_argument("--host", help="Server host")
    start_parser.add_argument("--port", type=int, help="Server port")
    start_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    start_parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    
    start_prod_parser = subparsers.add_parser("start-prod", help="Start production server")
    start_prod_parser.add_argument("--host", help="Server host")
    start_prod_parser.add_argument("--port", type=int, help="Server port")
    start_prod_parser.add_argument("--config", help="Configuration file")
    
    health_parser = subparsers.add_parser("health", help="Check server health")
    health_parser.add_argument("--host", default="localhost", help="Server host")
    health_parser.add_argument("--port", type=int, default=3456, help="Server port")
    
    # Utility commands
    clean_parser = subparsers.add_parser("clean", help="Clean build artifacts")
    
    deps_parser = subparsers.add_parser("deps", help="Manage dependencies")
    deps_parser.add_argument("--update", action="store_true", help="Update dependencies")
    deps_parser.add_argument("--dev", action="store_true", help="Include development dependencies")
    
    docs_parser = subparsers.add_parser("docs", help="Generate documentation")
    
    db_reset_parser = subparsers.add_parser("db-reset", help="Reset development database")
    
    logs_parser = subparsers.add_parser("logs", help="Show server logs")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs")
    logs_parser.add_argument("-n", "--lines", type=int, help="Number of lines to show")
    
    shell_parser = subparsers.add_parser("shell", help="Start interactive shell")
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create CLI instance
    cli = DevCLI()
    
    # Check virtual environment
    cli.check_venv()
    
    # Execute command
    command_method = getattr(cli, args.command.replace("-", "_"), None)
    if command_method:
        command_method(args)
    else:
        cli.log(f"Unknown command: {args.command}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()