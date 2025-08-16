#!/usr/bin/env python3
"""
Environment Setup Script

Sets up the development environment for MCP Jive.
"""

import sys
import os
import shutil
import argparse
import subprocess
from pathlib import Path

# Project root directory
project_root = Path(__file__).parent.parent.parent

def main():
    parser = argparse.ArgumentParser(description="Setup MCP Jive development environment")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force overwrite existing configuration")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    parser.add_argument("--skip-env", action="store_true",
                       help="Skip .env file creation")
    parser.add_argument("--skip-dirs", action="store_true",
                       help="Skip directory creation")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup(
        force=args.force,
        skip_deps=args.skip_deps,
        skip_env=args.skip_env,
        skip_dirs=args.skip_dirs,
        verbose=args.verbose
    )
    
    try:
        return setup.run()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        return 130
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1

class EnvironmentSetup:
    def __init__(self, force=False, skip_deps=False, skip_env=False, 
                 skip_dirs=False, verbose=False):
        self.force = force
        self.skip_deps = skip_deps
        self.skip_env = skip_env
        self.skip_dirs = skip_dirs
        self.verbose = verbose
        
    def log(self, message, level="info"):
        """Log a message"""
        if level == "error":
            print(f"❌ {message}")
        elif level == "warning":
            print(f"⚠️  {message}")
        elif level == "success":
            print(f"✅ {message}")
        elif self.verbose or level == "info":
            print(f"ℹ️  {message}")
    
    def run(self):
        """Run the environment setup"""
        print("🚀 Setting up MCP Jive development environment")
        print("=" * 50)
        
        success = True
        
        # Check prerequisites
        if not self._check_prerequisites():
            return 1
        
        # Create directories
        if not self.skip_dirs:
            success &= self._create_directories()
        
        # Setup environment file
        if not self.skip_env:
            success &= self._setup_env_file()
        
        # Install dependencies
        if not self.skip_deps:
            success &= self._install_dependencies()
        
        # Setup git hooks (if git repo)
        success &= self._setup_git_hooks()
        
        # Create initial configuration
        success &= self._create_initial_config()
        
        # Final validation
        success &= self._validate_setup()
        
        if success:
            self._print_success_message()
            return 0
        else:
            self.log("Setup completed with some issues", "warning")
            return 1
    
    def _check_prerequisites(self):
        """Check system prerequisites"""
        self.log("Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}", "error")
            return False
        
        self.log(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ✓")
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            self.log("pip available ✓")
        except subprocess.CalledProcessError:
            self.log("pip not available", "error")
            return False
        
        # Check git (optional)
        try:
            subprocess.run(["git", "--version"], 
                         capture_output=True, check=True)
            self.log("git available ✓")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("git not available (optional)", "warning")
        
        return True
    
    def _create_directories(self):
        """Create necessary directories"""
        self.log("Creating directories...")
        
        directories = [
            "data",
            "logs",
            "tmp",
            "backups",
            "config"
        ]
        
        for dir_name in directories:
            dir_path = project_root / dir_name
            try:
                dir_path.mkdir(exist_ok=True)
                self.log(f"Created directory: {dir_path}")
            except Exception as e:
                self.log(f"Failed to create directory {dir_path}: {e}", "error")
                return False
        
        return True
    
    def _setup_env_file(self):
        """Setup environment file"""
        self.log("Setting up environment file...")
        
        env_file = project_root / ".env"
        env_example = project_root / ".env.example"
        
        if env_file.exists() and not self.force:
            self.log(".env file already exists (use --force to overwrite)")
            return True
        
        if env_example.exists():
            try:
                shutil.copy2(env_example, env_file)
                self.log(f"Created .env from .env.example", "success")
            except Exception as e:
                self.log(f"Failed to copy .env.example: {e}", "error")
                return False
        else:
            # Create basic .env file
            env_content = """
# MCP Jive Environment Configuration

# Development settings
MCP_JIVE_DEBUG=true
MCP_JIVE_LOG_LEVEL=INFO

# Server settings
MCP_JIVE_HOST=localhost
MCP_JIVE_PORT=3454

# Database settings
MCP_JIVE_DATA_DIR=./data

# Tool settings
MCP_JIVE_CONSOLIDATED_TOOLS=false
MCP_JIVE_AI_ENABLED=true

# Add your custom settings below
""".strip()
            
            try:
                with open(env_file, 'w') as f:
                    f.write(env_content)
                self.log("Created basic .env file", "success")
            except Exception as e:
                self.log(f"Failed to create .env file: {e}", "error")
                return False
        
        return True
    
    def _install_dependencies(self):
        """Install Python dependencies"""
        self.log("Installing dependencies...")
        
        requirements_file = project_root / "requirements.txt"
        if not requirements_file.exists():
            self.log("requirements.txt not found", "warning")
            return True
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            if self.verbose:
                result = subprocess.run(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                self.log("Dependencies installed successfully", "success")
                return True
            else:
                self.log("Failed to install dependencies", "error")
                if not self.verbose and result.stderr:
                    self.log(f"Error: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            self.log(f"Error installing dependencies: {e}", "error")
            return False
    
    def _setup_git_hooks(self):
        """Setup git hooks if in a git repository"""
        git_dir = project_root / ".git"
        if not git_dir.exists():
            self.log("Not a git repository, skipping git hooks")
            return True
        
        self.log("Setting up git hooks...")
        
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        # Create pre-commit hook
        pre_commit_hook = hooks_dir / "pre-commit"
        pre_commit_content = """
#!/bin/bash
# MCP Jive pre-commit hook

echo "Running pre-commit checks..."

# Run basic validation
python bin/mcp-jive tools validate-config --env
if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed"
    exit 1
fi

# Run health check
python bin/mcp-jive tools health-check --quick
if [ $? -ne 0 ]; then
    echo "❌ Health check failed"
    exit 1
fi

echo "✅ Pre-commit checks passed"
exit 0
""".strip()
        
        try:
            with open(pre_commit_hook, 'w') as f:
                f.write(pre_commit_content)
            pre_commit_hook.chmod(0o755)
            self.log("Created pre-commit hook", "success")
        except Exception as e:
            self.log(f"Failed to create pre-commit hook: {e}", "warning")
        
        return True
    
    def _create_initial_config(self):
        """Create initial configuration files"""
        self.log("Creating initial configuration...")
        
        config_dir = project_root / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create development config
        dev_config = {
            "server": {
                "host": "localhost",
                "port": 3454,
                "mode": "stdio"
            },
            "database": {
                "type": "lancedb",
                "path": "./data"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "tools": {
                "enabled": True,
                "consolidated": False
            }
        }
        
        try:
            import json
            config_file = config_dir / "development.json"
            with open(config_file, 'w') as f:
                json.dump(dev_config, f, indent=2)
            self.log(f"Created development config: {config_file}", "success")
        except Exception as e:
            self.log(f"Failed to create development config: {e}", "warning")
        
        return True
    
    def _validate_setup(self):
        """Validate the setup"""
        self.log("Validating setup...")
        
        # Check if unified CLI is executable
        cli_path = project_root / "bin" / "mcp-jive"
        if cli_path.exists() and os.access(cli_path, os.X_OK):
            self.log("Unified CLI is executable ✓")
        else:
            self.log("Unified CLI is not executable", "warning")
        
        # Try to import main modules
        try:
            sys.path.insert(0, str(project_root / "src"))
            import mcp_jive
            self.log("Main module imports successfully ✓")
        except ImportError as e:
            self.log(f"Failed to import main module: {e}", "warning")
        
        return True
    
    def _print_success_message(self):
        """Print success message with next steps"""
        print("\n" + "=" * 50)
        print("🎉 Environment setup completed successfully!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Review and customize .env file if needed")
        print("2. Test the installation:")
        print("   ./bin/mcp-jive tools health-check")
        print("3. Start the development server:")
        print("   ./bin/mcp-jive dev server")
        print("4. Or start the main server:")
        print("   ./bin/mcp-jive server start")
        print("\nFor help with commands:")
        print("   ./bin/mcp-jive --help")
        print("\nHappy coding! 🚀")

if __name__ == "__main__":
    sys.exit(main())