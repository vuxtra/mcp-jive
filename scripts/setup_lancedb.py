#!/usr/bin/env python3
"""
LanceDB Setup Script

This script helps set up LanceDB for MCP Jive by:
1. Installing required dependencies
2. Creating necessary directories
3. Downloading embedding models
4. Initializing database schemas
5. Validating the setup

Usage:
    python scripts/setup_lancedb.py [--force] [--dev-mode]

Options:
    --force: Force reinstallation of dependencies
    --dev-mode: Setup for development environment
    --skip-models: Skip downloading embedding models
    --validate-only: Only run validation, skip setup
"""

import asyncio
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LanceDBSetup:
    """LanceDB setup and configuration manager."""
    
    def __init__(self, force: bool = False, dev_mode: bool = False, skip_models: bool = False):
        self.force = force
        self.dev_mode = dev_mode
        self.skip_models = skip_models
        self.project_root = Path(__file__).parent.parent
        self.setup_results = []
    
    def log_step(self, step_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log setup step result."""
        status = "✅" if success else "❌"
        logger.info(f"{status} {step_name}: {message}")
        
        self.setup_results.append({
            'step': step_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        try:
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 9):
                self.log_step(
                    "Python Version Check",
                    False,
                    f"Python 3.9+ required, found {version.major}.{version.minor}"
                )
                return False
            
            self.log_step(
                "Python Version Check",
                True,
                f"Python {version.major}.{version.minor}.{version.micro} is compatible"
            )
            return True
            
        except Exception as e:
            self.log_step("Python Version Check", False, f"Failed to check Python version: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        try:
            requirements_file = self.project_root / "requirements.txt"
            
            if not requirements_file.exists():
                self.log_step(
                    "Install Dependencies",
                    False,
                    "requirements.txt not found"
                )
                return False
            
            # Install dependencies
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            if self.force:
                cmd.extend(["--force-reinstall", "--no-cache-dir"])
            
            logger.info(f"Installing dependencies: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_step(
                    "Install Dependencies",
                    False,
                    f"pip install failed: {result.stderr}",
                    {'stdout': result.stdout, 'stderr': result.stderr}
                )
                return False
            
            self.log_step(
                "Install Dependencies",
                True,
                "All dependencies installed successfully"
            )
            return True
            
        except Exception as e:
            self.log_step("Install Dependencies", False, f"Failed to install dependencies: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        try:
            directories = [
                "data",
                "data/lancedb",
                "data/lancedb_jive",
                "logs",
                "backups",
                "cache",
                "cache/models"
            ]
            
            created_dirs = []
            for dir_name in directories:
                dir_path = self.project_root / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(str(dir_path))
                    logger.info(f"📁 Created directory: {dir_path}")
            
            self.log_step(
                "Create Directories",
                True,
                f"Created {len(created_dirs)} directories",
                {'created_directories': created_dirs}
            )
            return True
            
        except Exception as e:
            self.log_step("Create Directories", False, f"Failed to create directories: {e}")
            return False
    
    def download_embedding_models(self) -> bool:
        """Download and cache embedding models."""
        if self.skip_models:
            self.log_step(
                "Download Embedding Models",
                True,
                "Skipped model download (--skip-models flag)"
            )
            return True
        
        try:
            # Import sentence-transformers to download model
            logger.info("🤖 Downloading sentence-transformers model...")
            
            # Use subprocess to avoid import issues
            download_script = '''
import sys
try:
    from sentence_transformers import SentenceTransformer
    print("Downloading all-MiniLM-L6-v2 model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model downloaded successfully")
    print(f"Model path: {model._modules['0'].auto_model.config._name_or_path}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
'''
            
            result = subprocess.run(
                [sys.executable, "-c", download_script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                self.log_step(
                    "Download Embedding Models",
                    False,
                    f"Model download failed: {result.stderr}",
                    {'stdout': result.stdout, 'stderr': result.stderr}
                )
                return False
            
            self.log_step(
                "Download Embedding Models",
                True,
                "all-MiniLM-L6-v2 model downloaded successfully",
                {'model_info': result.stdout}
            )
            return True
            
        except subprocess.TimeoutExpired:
            self.log_step(
                "Download Embedding Models",
                False,
                "Model download timed out (5 minutes)"
            )
            return False
        except Exception as e:
            self.log_step("Download Embedding Models", False, f"Failed to download models: {e}")
            return False
    
    async def initialize_databases(self) -> bool:
        """Initialize LanceDB databases and schemas."""
        try:
            # Import LanceDB managers
            try:
                from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig
                from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager
                from mcp_jive.lancedb_manager import DatabaseConfig as JiveDatabaseConfig
            except ImportError as e:
                self.log_step(
                    "Initialize Databases",
                    False,
                    f"Cannot import LanceDB managers: {e}"
                )
                return False
            
            # Initialize Server LanceDB
            logger.info("🗄️ Initializing Server LanceDB...")
            server_config = DatabaseConfig(
                data_path=str(self.project_root / "data" / "lancedb"),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            server_manager = LanceDBManager(server_config)
            await server_manager.initialize()
            
            # Initialize Jive LanceDB
            logger.info("🗄️ Initializing Jive LanceDB...")
            jive_config = JiveDatabaseConfig(
                data_path=str(self.project_root / "data" / "lancedb_jive"),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            jive_manager = JiveLanceDBManager(jive_config)
            await jive_manager.initialize()
            
            # Get health status
            server_health = server_manager.get_health_status()
            jive_health = jive_manager.get_health_status()
            
            # Cleanup
            await server_manager.cleanup()
            await jive_manager.cleanup()
            
            if server_health['status'] not in ['healthy', 'degraded'] or jive_health['status'] not in ['healthy', 'degraded']:
                self.log_step(
                    "Initialize Databases",
                    False,
                    "Database initialization failed health check",
                    {'server_health': server_health, 'jive_health': jive_health}
                )
                return False
            
            self.log_step(
                "Initialize Databases",
                True,
                "Both databases initialized successfully",
                {
                    'server_tables': server_health.get('tables', {}),
                    'jive_tables': jive_health.get('tables', {})
                }
            )
            return True
            
        except Exception as e:
            self.log_step("Initialize Databases", False, f"Failed to initialize databases: {e}")
            return False
    
    def create_configuration_files(self) -> bool:
        """Create or update configuration files."""
        try:
            # Create .env.lancedb if it doesn't exist
            env_lancedb = self.project_root / ".env.lancedb"
            if env_lancedb.exists():
                logger.info("📄 .env.lancedb already exists")
            else:
                self.log_step(
                    "Create Configuration Files",
                    False,
                    ".env.lancedb template not found"
                )
                return False
            
            # Update .env.dev if in dev mode
            if self.dev_mode:
                env_dev = self.project_root / ".env.dev"
                if env_dev.exists():
                    # Backup original
                    backup_file = self.project_root / f".env.dev.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    env_dev.rename(backup_file)
                    logger.info(f"📄 Backed up .env.dev to {backup_file.name}")
                
                # Copy LanceDB configuration
                with open(env_lancedb, 'r') as src, open(env_dev, 'w') as dst:
                    dst.write(src.read())
                
                logger.info("📄 Updated .env.dev with LanceDB configuration")
            
            self.log_step(
                "Create Configuration Files",
                True,
                "Configuration files ready"
            )
            return True
            
        except Exception as e:
            self.log_step("Create Configuration Files", False, f"Failed to create config files: {e}")
            return False
    
    async def validate_setup(self) -> bool:
        """Validate the complete setup."""
        try:
            # Run basic validation
            validation_script = self.project_root / "scripts" / "validate_lancedb_migration.py"
            
            if not validation_script.exists():
                self.log_step(
                    "Validate Setup",
                    False,
                    "Validation script not found"
                )
                return False
            
            # Run validation with basic tests only
            logger.info("🔍 Running setup validation...")
            result = subprocess.run(
                [sys.executable, str(validation_script), "--validate-only"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            
            self.log_step(
                "Validate Setup",
                success,
                "Setup validation passed" if success else "Setup validation failed",
                {
                    'validation_output': result.stdout,
                    'validation_errors': result.stderr
                }
            )
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_step(
                "Validate Setup",
                False,
                "Setup validation timed out"
            )
            return False
        except Exception as e:
            self.log_step("Validate Setup", False, f"Failed to validate setup: {e}")
            return False
    
    async def run_setup(self) -> Dict[str, Any]:
        """Run the complete setup process."""
        logger.info("🚀 Starting LanceDB setup...")
        
        setup_steps = [
            ("Python Version Check", self.check_python_version),
            ("Install Dependencies", self.install_dependencies),
            ("Create Directories", self.create_directories),
            ("Download Embedding Models", self.download_embedding_models),
            ("Initialize Databases", self.initialize_databases),
            ("Create Configuration Files", self.create_configuration_files),
            ("Validate Setup", self.validate_setup)
        ]
        
        for step_name, step_func in setup_steps:
            logger.info(f"🔄 Running: {step_name}")
            
            try:
                if asyncio.iscoroutinefunction(step_func):
                    success = await step_func()
                else:
                    success = step_func()
                
                if not success:
                    logger.error(f"❌ Setup failed at step: {step_name}")
                    break
                    
            except Exception as e:
                self.log_step(step_name, False, f"Step failed with exception: {e}")
                logger.error(f"❌ Setup failed at step: {step_name} - {e}")
                break
        
        # Generate summary
        total_steps = len(self.setup_results)
        successful_steps = sum(1 for result in self.setup_results if result['success'])
        failed_steps = total_steps - successful_steps
        
        summary = {
            'success': failed_steps == 0,
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'failed_steps': failed_steps,
            'setup_results': self.setup_results
        }
        
        return summary

def print_setup_report(summary: Dict[str, Any]):
    """Print detailed setup report."""
    print("\n" + "="*60)
    print("🔧 LANCEDB SETUP REPORT")
    print("="*60)
    
    status = "✅ SUCCESS" if summary['success'] else "❌ FAILURE"
    print(f"Overall Status: {status}")
    print(f"Steps Completed: {summary['successful_steps']}/{summary['total_steps']}")
    
    if summary['failed_steps'] > 0:
        print(f"Steps Failed: {summary['failed_steps']}")
        print("\n❌ Failed Steps:")
        for result in summary['setup_results']:
            if not result['success']:
                print(f"  • {result['step']}: {result['message']}")
    
    print("\n📋 Setup Steps:")
    for result in summary['setup_results']:
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {status_icon} {result['step']}: {result['message']}")
    
    print("\n" + "="*60)
    
    if summary['success']:
        print("🎉 LanceDB setup completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Run migration: python scripts/migrate_weaviate_to_lancedb.py")
        print("  2. Validate migration: python scripts/validate_lancedb_migration.py")
        print("  3. Update application imports to use LanceDBManager")
        print("  4. Test your application with the new database")
    else:
        print("⚠️ LanceDB setup failed!")
        print("\n🔧 Recommended actions:")
        print("  1. Review failed step details above")
        print("  2. Check system requirements and dependencies")
        print("  3. Ensure sufficient disk space and permissions")
        print("  4. Re-run setup after resolving issues")

async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Setup LanceDB for MCP Jive')
    parser.add_argument('--force', action='store_true', help='Force reinstallation of dependencies')
    parser.add_argument('--dev-mode', action='store_true', help='Setup for development environment')
    parser.add_argument('--skip-models', action='store_true', help='Skip downloading embedding models')
    parser.add_argument('--validate-only', action='store_true', help='Only run validation, skip setup')
    
    args = parser.parse_args()
    
    try:
        if args.validate_only:
            # Just run validation
            logger.info("🔍 Running validation only...")
            validation_script = Path(__file__).parent / "validate_lancedb_migration.py"
            
            if not validation_script.exists():
                print("❌ Validation script not found")
                sys.exit(1)
            
            result = subprocess.run(
                [sys.executable, str(validation_script)],
                timeout=120
            )
            sys.exit(result.returncode)
        
        # Run setup
        setup_manager = LanceDBSetup(
            force=args.force,
            dev_mode=args.dev_mode,
            skip_models=args.skip_models
        )
        
        summary = await setup_manager.run_setup()
        
        # Print report
        print_setup_report(summary)
        
        # Save detailed results
        results_file = f"setup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['success'] else 1)
        
    except Exception as e:
        logger.error(f"❌ Setup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())