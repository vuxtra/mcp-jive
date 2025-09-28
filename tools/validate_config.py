#!/usr/bin/env python3
"""
Configuration Validation Tool

Validates MCP Jive configuration files and environment setup.
"""

import sys
import os
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    parser = argparse.ArgumentParser(description="Validate MCP Jive configuration")
    parser.add_argument("--config", "-c", type=str,
                       help="Path to configuration file")
    parser.add_argument("--env", "-e", action="store_true",
                       help="Validate environment variables")
    parser.add_argument("--database", "-d", action="store_true",
                       help="Validate database configuration")
    parser.add_argument("--tools", "-t", action="store_true",
                       help="Validate tools configuration")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Validate all configurations")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.all:
        args.env = args.database = args.tools = True
    
    if not any([args.config, args.env, args.database, args.tools]):
        parser.print_help()
        return 1
    
    validator = ConfigValidator(verbose=args.verbose)
    success = True
    
    try:
        if args.config:
            success &= validator.validate_config_file(args.config)
        
        if args.env:
            success &= validator.validate_environment()
        
        if args.database:
            success &= validator.validate_database_config()
        
        if args.tools:
            success &= validator.validate_tools_config()
        
        if success:
            print("\n✅ All validations passed!")
            return 0
        else:
            print("\n❌ Some validations failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        return 1

class ConfigValidator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def log(self, message: str, level: str = "info"):
        if level == "error":
            self.errors.append(message)
            print(f"❌ {message}")
        elif level == "warning":
            self.warnings.append(message)
            print(f"⚠️  {message}")
        elif self.verbose:
            print(f"ℹ️  {message}")
    
    def validate_config_file(self, config_path: str) -> bool:
        """Validate a configuration file"""
        print(f"\n🔍 Validating configuration file: {config_path}")
        
        config_file = Path(config_path)
        if not config_file.exists():
            self.log(f"Configuration file not found: {config_path}", "error")
            return False
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() in ['.yml', '.yaml']:
                    config = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    self.log(f"Unsupported config file format: {config_file.suffix}", "error")
                    return False
            
            self.log(f"Configuration file loaded successfully")
            return self._validate_config_structure(config)
            
        except Exception as e:
            self.log(f"Failed to parse configuration file: {e}", "error")
            return False
    
    def validate_environment(self) -> bool:
        """Validate environment variables"""
        print("\n🔍 Validating environment variables")
        
        required_vars = [
            "PYTHONPATH",
        ]
        
        optional_vars = [
            "MCP_JIVE_DEBUG",
            "MCP_JIVE_LOG_LEVEL",
            "MCP_JIVE_CONSOLIDATED_TOOLS",
            "MCP_JIVE_AI_ENABLED",
            "MCP_JIVE_CONFIG_PATH",
        ]
        
        success = True
        
        # Check required variables
        for var in required_vars:
            if var not in os.environ:
                self.log(f"Required environment variable missing: {var}", "error")
                success = False
            else:
                self.log(f"Found required variable: {var}")
        
        # Check optional variables
        for var in optional_vars:
            if var in os.environ:
                self.log(f"Found optional variable: {var} = {os.environ[var]}")
            else:
                self.log(f"Optional variable not set: {var}")
        
        # Validate .env.example exists
        env_example = project_root / ".env.example"
        if env_example.exists():
            self.log("Found .env.example file")
        else:
            self.log(".env.example file not found", "warning")
        
        return success
    
    def validate_database_config(self) -> bool:
        """Validate database configuration"""
        print("\n🔍 Validating database configuration")
        
        success = True
        
        # Check data directory
        data_dir = project_root / "data"
        if data_dir.exists():
            self.log(f"Data directory exists: {data_dir}")
            
            # Check for database files
            db_files = list(data_dir.glob("**/*"))
            if db_files:
                self.log(f"Found {len(db_files)} database files")
            else:
                self.log("Data directory is empty", "warning")
        else:
            self.log("Data directory does not exist (will be created on first run)")
        
        # Check database modules
        try:
            sys.path.insert(0, str(project_root / "src"))
            from mcp_jive import database
            self.log("Database module imports successfully")
        except ImportError as e:
            self.log(f"Failed to import database module: {e}", "error")
            success = False
        
        return success
    
    def validate_tools_config(self) -> bool:
        """Validate tools configuration"""
        print("\n🔍 Validating tools configuration")
        
        success = True
        
        # Check tools directory
        tools_dir = project_root / "src" / "mcp_jive" / "tools"
        if tools_dir.exists():
            self.log(f"Tools directory exists: {tools_dir}")
            
            # Count tool files
            tool_files = list(tools_dir.glob("*.py"))
            tool_files = [f for f in tool_files if f.name != "__init__.py"]
            self.log(f"Found {len(tool_files)} tool files")
            
            if self.verbose:
                for tool_file in tool_files:
                    self.log(f"  - {tool_file.name}")
        else:
            self.log("Tools directory not found", "error")
            success = False
        
        # Check for consolidated tools environment
        if os.environ.get("MCP_JIVE_CONSOLIDATED_TOOLS") == "true":
            expected_count = int(os.environ.get("MCP_JIVE_TOOL_COUNT", "7"))
            self.log(f"Consolidated tools mode enabled (expecting {expected_count} tools)")
        
        return success
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> bool:
        """Validate the structure of a configuration object"""
        success = True
        
        # Define expected configuration sections
        expected_sections = {
            "server": ["host", "port", "mode"],
            "database": ["type", "path"],
            "logging": ["level", "format"],
            "tools": ["enabled", "consolidated"]
        }
        
        for section, fields in expected_sections.items():
            if section in config:
                self.log(f"Found configuration section: {section}")
                
                section_config = config[section]
                for field in fields:
                    if field in section_config:
                        self.log(f"  - {field}: {section_config[field]}")
                    else:
                        self.log(f"  - Missing field in {section}: {field}", "warning")
            else:
                self.log(f"Missing configuration section: {section}", "warning")
        
        return success

if __name__ == "__main__":
    sys.exit(main())