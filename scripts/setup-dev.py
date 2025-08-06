#!/usr/bin/env python3
"""
MCP Jive Development Environment Setup Script

This script automates the setup of a complete development environment for MCP Jive,
including Python virtual environment, dependencies, configuration, and development tools.

Usage:
    python scripts/setup-dev.py [options]

Options:
    --python PATH       Specify Python interpreter path
    --no-editor        Skip editor configuration setup
    --verbose          Enable verbose output
    --reset            Reset existing environment
    --help             Show this help message
"""

import argparse
import os
import subprocess
import sys
import shutil
import json
from pathlib import Path
from typing import Optional, List


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class DevSetup:
    """Main development environment setup class."""
    
    def __init__(self, args):
        self.args = args
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.verbose = args.verbose
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with color coding."""
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED
        }
        color = colors.get(level, Colors.BLUE)
        print(f"{color}[{level}]{Colors.END} {message}")
        
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command with optional verbose output."""
        if self.verbose:
            self.log(f"Running: {' '.join(cmd)}", "INFO")
            
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                check=check,
                capture_output=not self.verbose,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {' '.join(cmd)}", "ERROR")
            if not self.verbose and e.stdout:
                print(e.stdout)
            if not self.verbose and e.stderr:
                print(e.stderr)
            raise
            
    def check_python_version(self) -> str:
        """Check and validate Python version."""
        python_cmd = self.args.python or sys.executable
        
        try:
            result = self.run_command([python_cmd, "--version"])
            version_output = result.stdout.strip() if result.stdout else ""
            
            # Extract version number
            import re
            version_match = re.search(r'Python (\d+)\.(\d+)\.(\d+)', version_output)
            if not version_match:
                raise ValueError(f"Could not parse Python version: {version_output}")
                
            major, minor, patch = map(int, version_match.groups())
            
            if major < 3 or (major == 3 and minor < 9):
                raise ValueError(f"Python 3.9+ required, found {major}.{minor}.{patch}")
                
            self.log(f"Python version: {major}.{minor}.{patch} ✓", "SUCCESS")
            return python_cmd
            
        except (subprocess.CalledProcessError, ValueError) as e:
            self.log(f"Python version check failed: {e}", "ERROR")
            sys.exit(1)
            
    def create_virtual_environment(self, python_cmd: str):
        """Create Python virtual environment."""
        if self.venv_path.exists():
            if self.args.reset:
                self.log("Removing existing virtual environment...", "WARNING")
                shutil.rmtree(self.venv_path)
            else:
                self.log("Virtual environment already exists (use --reset to recreate)", "WARNING")
                return
                
        self.log("Creating virtual environment...", "INFO")
        self.run_command([python_cmd, "-m", "venv", str(self.venv_path)])
        self.log("Virtual environment created ✓", "SUCCESS")
        
    def get_venv_python(self) -> str:
        """Get path to Python executable in virtual environment."""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "python.exe")
        else:  # Unix-like
            return str(self.venv_path / "bin" / "python")
            
    def get_venv_pip(self) -> str:
        """Get path to pip executable in virtual environment."""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:  # Unix-like
            return str(self.venv_path / "bin" / "pip")
            
    def install_dependencies(self):
        """Install Python dependencies."""
        pip_cmd = self.get_venv_pip()
        
        # Upgrade pip first
        self.log("Upgrading pip...", "INFO")
        self.run_command([pip_cmd, "install", "--upgrade", "pip"])
        
        # Install main dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            self.log("Installing main dependencies...", "INFO")
            self.run_command([pip_cmd, "install", "-r", str(requirements_file)])
            
        # Install development dependencies
        self.log("Installing development dependencies...", "INFO")
        dev_deps = [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
            "flake8>=6.1.0",
            "coverage>=7.3.0",
            "bandit>=1.7.0",
            "safety>=2.3.0",
            "pre-commit>=3.5.0"
        ]
        self.run_command([pip_cmd, "install"] + dev_deps)
        
        # Install package in development mode
        self.log("Installing mcp-jive in development mode...", "INFO")
        self.run_command([pip_cmd, "install", "-e", "."])
        
        self.log("Dependencies installed ✓", "SUCCESS")
        
    def create_environment_files(self):
        """Create development environment configuration files."""
        # Create .env.dev from template
        env_dev_path = self.project_root / ".env.dev"
        if not env_dev_path.exists():
            self.log("Creating .env.dev file...", "INFO")
            env_content = '''# MCP Jive Development Environment
# This file is automatically generated by setup-dev.py

# Development Mode
MCP_ENV=development
MCP_DEV_MODE=true
MCP_LOG_LEVEL=DEBUG
MCP_AUTO_RELOAD=true
MCP_DETAILED_ERRORS=true

# Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=3456
MCP_MAX_CONNECTIONS=10
MCP_REQUEST_TIMEOUT=30

# Weaviate Database (Embedded)
WEAVIATE_USE_EMBEDDED=true
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_TIMEOUT=30

# Development Features
MCP_HEALTH_CHECK_ENABLED=true
MCP_METRICS_ENABLED=true
MCP_CORS_ENABLED=true
MCP_CORS_ORIGINS=http://localhost:3456,http://127.0.0.1:3456

# AI Provider Configuration (No longer required - using MCP client execution)

# Development Tools
MCP_RATE_LIMIT_ENABLED=false
MCP_AUTH_ENABLED=false
'''
            env_dev_path.write_text(env_content)
            self.log(".env.dev created ✓", "SUCCESS")
        else:
            self.log(".env.dev already exists", "WARNING")
            
    def setup_editor_config(self):
        """Setup editor configurations."""
        if self.args.no_editor:
            self.log("Skipping editor configuration", "INFO")
            return
            
        # VSCode configuration
        vscode_dir = self.project_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # VSCode settings
        settings_file = vscode_dir / "settings.json"
        if not settings_file.exists():
            self.log("Creating VSCode settings...", "INFO")
            settings = {
                "python.defaultInterpreterPath": "./venv/bin/python",
                "python.linting.enabled": True,
                "python.linting.flake8Enabled": True,
                "python.formatting.provider": "black",
                "python.sortImports.args": ["--profile", "black"],
                "files.exclude": {
                    "**/__pycache__": True,
                    "**/venv": True,
                    "data/": True,
                    "*.pyc": True
                },
                "editor.formatOnSave": True,
                "editor.codeActionsOnSave": {
                    "source.organizeImports": True
                }
            }
            settings_file.write_text(json.dumps(settings, indent=2))
            
        # VSCode launch configuration
        launch_file = vscode_dir / "launch.json"
        if not launch_file.exists():
            launch_config = {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "MCP Jive Server",
                        "type": "python",
                        "request": "launch",
                        "program": "${workspaceFolder}/src/main.py",
                        "console": "integratedTerminal",
                        "env": {
                            "PYTHONPATH": "${workspaceFolder}/src"
                        },
                        "args": ["--dev"]
                    }
                ]
            }
            launch_file.write_text(json.dumps(launch_config, indent=2))
            
        # VSCode extensions
        extensions_file = vscode_dir / "extensions.json"
        if not extensions_file.exists():
            extensions = {
                "recommendations": [
                    "ms-python.python",
                    "ms-python.black-formatter",
                    "ms-python.isort",
                    "ms-python.mypy-type-checker",
                    "ms-python.flake8",
                    "redhat.vscode-yaml",
                    "ms-vscode.vscode-json"
                ]
            }
            extensions_file.write_text(json.dumps(extensions, indent=2))
            
        self.log("VSCode configuration created ✓", "SUCCESS")
        
    def create_development_scripts(self):
        """Create development utility scripts."""
        scripts_dir = self.project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Create development CLI wrapper
        dev_cli_path = scripts_dir / "dev.py"
        if not dev_cli_path.exists():
            self.log("Creating development CLI...", "INFO")
            dev_cli_content = '''#!/usr/bin/env python3
"""
MCP Jive Development CLI

Provides convenient commands for development tasks.
"""

import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
venv_python = project_root / "venv" / "bin" / "python"

def run_cmd(cmd):
    """Run a command in the virtual environment."""
    subprocess.run([str(venv_python)] + cmd, cwd=project_root)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/dev.py <command>")
        print("Commands: test, lint, format, type-check, start, health")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "test":
        run_cmd(["-m", "pytest", "tests/"])
    elif command == "test-unit":
        run_cmd(["-m", "pytest", "tests/unit/"])
    elif command == "test-integration":
        run_cmd(["-m", "pytest", "tests/integration/"])
    elif command == "lint":
        run_cmd(["-m", "flake8", "src/", "tests/"])
    elif command == "format":
        run_cmd(["-m", "black", "src/", "tests/", "scripts/"])
        run_cmd(["-m", "isort", "src/", "tests/", "scripts/"])
    elif command == "type-check":
        run_cmd(["-m", "mypy", "src/"])
    elif command == "start":
        run_cmd(["-m", "src.main", "--dev"])
    elif command == "health":
        run_cmd(["-m", "scripts.health_check"])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
'''
            dev_cli_path.write_text(dev_cli_content)
            dev_cli_path.chmod(0o755)
            
        self.log("Development scripts created ✓", "SUCCESS")
        
    def create_test_structure(self):
        """Create test directory structure."""
        tests_dir = self.project_root / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create test subdirectories
        for subdir in ["unit", "integration", "mcp"]:
            (tests_dir / subdir).mkdir(exist_ok=True)
            (tests_dir / subdir / "__init__.py").touch()
            
        # Create conftest.py
        conftest_path = tests_dir / "conftest.py"
        if not conftest_path.exists():
            conftest_content = '''"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path

# Test configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def test_data_dir(project_root):
    """Get the test data directory."""
    return project_root / "tests" / "data"
'''
            conftest_path.write_text(conftest_content)
            
        self.log("Test structure created ✓", "SUCCESS")
        
    def validate_setup(self):
        """Validate the development environment setup."""
        self.log("Validating development environment...", "INFO")
        
        # Check virtual environment
        venv_python = self.get_venv_python()
        if not Path(venv_python).exists():
            self.log("Virtual environment Python not found", "ERROR")
            return False
            
        # Check if mcp-jive is installed
        try:
            result = self.run_command([venv_python, "-c", "import mcp_server; print('OK')"])
            if "OK" not in result.stdout:
                self.log("mcp-jive package not properly installed", "ERROR")
                return False
        except subprocess.CalledProcessError:
            self.log("mcp-jive package not properly installed", "ERROR")
            return False
            
        # Check development tools
        dev_tools = ["pytest", "black", "flake8", "mypy"]
        for tool in dev_tools:
            try:
                self.run_command([venv_python, "-m", tool, "--version"])
            except subprocess.CalledProcessError:
                self.log(f"Development tool {tool} not available", "ERROR")
                return False
                
        self.log("Development environment validation passed ✓", "SUCCESS")
        return True
        
    def print_next_steps(self):
        """Print next steps for the developer."""
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 Development environment setup complete!{Colors.END}\n")
        
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print(f"1. Activate the virtual environment:")
        if os.name == 'nt':
            print(f"   {Colors.BLUE}venv\\Scripts\\activate{Colors.END}")
        else:
            print(f"   {Colors.BLUE}source venv/bin/activate{Colors.END}")
            
        print(f"\n2. Start the development server:")
        print(f"   {Colors.BLUE}python scripts/dev.py start{Colors.END}")
        
        print(f"\n3. Run tests:")
        print(f"   {Colors.BLUE}python scripts/dev.py test{Colors.END}")
        
        print(f"\n4. Format code:")
        print(f"   {Colors.BLUE}python scripts/dev.py format{Colors.END}")
        
        print(f"\n5. Check code quality:")
        print(f"   {Colors.BLUE}python scripts/dev.py lint{Colors.END}")
        
        print(f"\n{Colors.YELLOW}📖 See docs/development/ for detailed guides{Colors.END}")
        
    def run(self):
        """Run the complete development environment setup."""
        try:
            self.log("Starting MCP Jive development environment setup...", "INFO")
            
            # Step 1: Check Python version
            python_cmd = self.check_python_version()
            
            # Step 2: Create virtual environment
            self.create_virtual_environment(python_cmd)
            
            # Step 3: Install dependencies
            self.install_dependencies()
            
            # Step 4: Create configuration files
            self.create_environment_files()
            
            # Step 5: Setup editor configuration
            self.setup_editor_config()
            
            # Step 6: Create development scripts
            self.create_development_scripts()
            
            # Step 7: Create test structure
            self.create_test_structure()
            
            # Step 8: Validate setup
            if not self.validate_setup():
                self.log("Setup validation failed", "ERROR")
                sys.exit(1)
                
            # Step 9: Print next steps
            self.print_next_steps()
            
        except KeyboardInterrupt:
            self.log("\nSetup interrupted by user", "WARNING")
            sys.exit(1)
        except Exception as e:
            self.log(f"Setup failed: {e}", "ERROR")
            if self.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup MCP Jive development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup-dev.py                    # Basic setup
  python scripts/setup-dev.py --verbose          # Verbose output
  python scripts/setup-dev.py --reset            # Reset existing environment
  python scripts/setup-dev.py --no-editor        # Skip editor setup
"""
    )
    
    parser.add_argument(
        "--python",
        help="Specify Python interpreter path"
    )
    parser.add_argument(
        "--no-editor",
        action="store_true",
        help="Skip editor configuration setup"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing environment"
    )
    
    args = parser.parse_args()
    
    setup = DevSetup(args)
    setup.run()


if __name__ == "__main__":
    main()