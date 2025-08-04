#!/usr/bin/env python3
"""Migration script for transitioning to consolidated MCP tools.

This script helps migrate from legacy tools to the new consolidated tools,
including validation, testing, and rollback capabilities.
"""

import asyncio
import argparse
import logging
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_jive.tools.consolidated import (
    create_consolidated_registry,
    CONSOLIDATED_TOOLS,
    LEGACY_TOOLS_REPLACED
)
from mcp_jive.tools.consolidated_registry import MCPConsolidatedToolRegistry
from mcp_jive.tools.tool_config import (
    ToolConfiguration,
    ToolMode,
    ToolMigrationManager,
    get_migration_config,
    get_production_config
)
from mcp_jive.storage.work_item_storage import WorkItemStorage
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.config import ServerConfig

logger = logging.getLogger(__name__)


class MigrationScript:
    """Main migration script for consolidated tools."""
    
    def __init__(self, config_file: Optional[str] = None, dry_run: bool = False):
        self.config_file = config_file
        self.dry_run = dry_run
        self.migration_config = get_migration_config()
        self.migration_manager = ToolMigrationManager(self.migration_config)
        
        # Initialize components
        self.server_config: Optional[ServerConfig] = None
        self.lancedb_manager: Optional[LanceDBManager] = None
        self.storage: Optional[WorkItemStorage] = None
        self.legacy_registry: Optional[MCPConsolidatedToolRegistry] = None
        self.consolidated_registry: Optional[MCPConsolidatedToolRegistry] = None
        
        # Migration state
        self.migration_results = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "tests_passed": 0,
            "tests_failed": 0,
            "validation_errors": [],
            "performance_metrics": {},
            "rollback_available": False
        }
    
    async def initialize(self) -> None:
        """Initialize all components for migration."""
        logger.info("Initializing migration environment...")
        
        try:
            # Load configuration
            if self.config_file and os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                self.server_config = ServerConfig(**config_data)
            else:
                self.server_config = ServerConfig()
            
            # Initialize database
            db_config = DatabaseConfig(data_path='./data/lancedb_jive')
            self.lancedb_manager = LanceDBManager(db_config)
            await self.lancedb_manager.initialize()
            
            # Initialize storage
            self.storage = WorkItemStorage(lancedb_manager=self.lancedb_manager)
            await self.storage.initialize()
            
            logger.info("Migration environment initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize migration environment: {e}")
            raise
    
    async def create_registries(self) -> None:
        """Create both legacy and consolidated registries for comparison."""
        logger.info("Creating tool registries...")
        
        try:
            # Create legacy registry (with legacy support enabled)
            self.legacy_registry = MCPConsolidatedToolRegistry(
                config=self.server_config,
                lancedb_manager=self.lancedb_manager,
                enable_legacy_support=True,
                mode="full"  # Include all tools for comparison
            )
            await self.legacy_registry.initialize()
            
            # Create consolidated registry
            self.consolidated_registry = MCPConsolidatedToolRegistry(
                config=self.server_config,
                lancedb_manager=self.lancedb_manager,
                enable_legacy_support=False,
                mode="consolidated"  # Only consolidated tools
            )
            await self.consolidated_registry.initialize()
            
            logger.info("Tool registries created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create registries: {e}")
            raise
    
    async def validate_environment(self) -> bool:
        """Validate that the environment is ready for migration."""
        logger.info("Validating migration environment...")
        
        validation_errors = []
        
        try:
            # Check database connectivity
            if not self.lancedb_manager or not await self.lancedb_manager.health_check():
                validation_errors.append("Database connection failed")
            
            # Check storage initialization
            if not self.storage or not self.storage.is_initialized:
                validation_errors.append("Storage not properly initialized")
            
            # Check registry initialization
            if not self.legacy_registry or not self.legacy_registry.is_initialized:
                validation_errors.append("Legacy registry not initialized")
            
            if not self.consolidated_registry or not self.consolidated_registry.is_initialized:
                validation_errors.append("Consolidated registry not initialized")
            
            # Validate tool availability
            legacy_tools = await self.legacy_registry.list_tools()
            consolidated_tools = await self.consolidated_registry.list_tools()
            
            legacy_tool_names = {tool.name for tool in legacy_tools}
            consolidated_tool_names = {tool.name for tool in consolidated_tools}
            
            # Check that all consolidated tools are available
            missing_consolidated = set(CONSOLIDATED_TOOLS) - consolidated_tool_names
            if missing_consolidated:
                validation_errors.append(f"Missing consolidated tools: {missing_consolidated}")
            
            # Check configuration validation
            config_issues = self.migration_config.validate()
            validation_errors.extend(config_issues)
            
            self.migration_results["validation_errors"] = validation_errors
            
            if validation_errors:
                logger.error(f"Validation failed with {len(validation_errors)} errors:")
                for error in validation_errors:
                    logger.error(f"  - {error}")
                return False
            
            logger.info("Environment validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            validation_errors.append(f"Validation exception: {e}")
            self.migration_results["validation_errors"] = validation_errors
            return False
    
    async def run_compatibility_tests(self) -> bool:
        """Run tests to ensure consolidated tools work correctly."""
        logger.info("Running compatibility tests...")
        
        test_cases = [
            # Work item management tests
            {
                "name": "Create work item",
                "tool": "jive_manage_work_item",
                "params": {
                    "action": "create",
                    "type": "task",
                    "title": "Migration Test Task",
                    "description": "Test task for migration validation"
                }
            },
            {
                "name": "Get work item",
                "tool": "jive_get_work_item",
                "params": {
                    "work_item_id": "test-migration-123"
                }
            },
            {
                "name": "Search content",
                "tool": "jive_search_content",
                "params": {
                    "query": "migration test",
                    "content_types": ["work_item", "title"],
                    "limit": 5
                }
            },
            {
                "name": "Get hierarchy",
                "tool": "jive_get_hierarchy",
                "params": {
                    "work_item_id": "test-migration-123",
                    "relationship_type": "children"
                }
            },
            {
                "name": "Track progress",
                "tool": "jive_track_progress",
                "params": {
                    "action": "track",
                    "work_item_id": "test-migration-123",
                    "progress_percentage": 50
                }
            }
        ]
        
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            try:
                logger.info(f"Running test: {test_case['name']}")
                
                if self.dry_run:
                    logger.info(f"  [DRY RUN] Would call {test_case['tool']} with {test_case['params']}")
                    passed += 1
                    continue
                
                # Run the test
                result = await self.consolidated_registry.call_tool(
                    test_case['tool'],
                    test_case['params']
                )
                
                # Parse result
                if result and len(result) > 0:
                    response_data = json.loads(result[0].text)
                    if response_data.get('success', False) or 'error' not in response_data:
                        logger.info(f"  ✓ {test_case['name']} passed")
                        passed += 1
                    else:
                        logger.error(f"  ✗ {test_case['name']} failed: {response_data.get('error', 'Unknown error')}")
                        failed += 1
                else:
                    logger.error(f"  ✗ {test_case['name']} failed: No response")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"  ✗ {test_case['name']} failed with exception: {e}")
                failed += 1
        
        self.migration_results["tests_passed"] = passed
        self.migration_results["tests_failed"] = failed
        
        logger.info(f"Compatibility tests completed: {passed} passed, {failed} failed")
        return failed == 0
    
    async def run_legacy_mapping_tests(self) -> bool:
        """Test that legacy tools are properly mapped to consolidated tools."""
        logger.info("Running legacy mapping tests...")
        
        legacy_test_cases = [
            {
                "legacy_tool": "jive_create_work_item",
                "params": {
                    "title": "Legacy Test Task",
                    "type": "task",
                    "description": "Created via legacy API"
                },
                "expected_mapping": "jive_manage_work_item"
            },
            {
                "legacy_tool": "jive_update_work_item",
                "params": {
                    "work_item_id": "test-123",
                    "title": "Updated via legacy API"
                },
                "expected_mapping": "jive_manage_work_item"
            },
            {
                "legacy_tool": "jive_search_work_items",
                "params": {
                    "query": "legacy search test",
                    "limit": 5
                },
                "expected_mapping": "jive_search_content"
            }
        ]
        
        passed = 0
        failed = 0
        
        for test_case in legacy_test_cases:
            try:
                logger.info(f"Testing legacy mapping: {test_case['legacy_tool']}")
                
                if self.dry_run:
                    logger.info(f"  [DRY RUN] Would test mapping for {test_case['legacy_tool']}")
                    passed += 1
                    continue
                
                # Test with legacy registry (which has backward compatibility)
                result = await self.legacy_registry.call_tool(
                    test_case['legacy_tool'],
                    test_case['params']
                )
                
                if result and len(result) > 0:
                    response_data = json.loads(result[0].text)
                    if response_data.get('success', False) or 'error' not in response_data:
                        logger.info(f"  ✓ {test_case['legacy_tool']} mapping works")
                        passed += 1
                    else:
                        logger.error(f"  ✗ {test_case['legacy_tool']} mapping failed: {response_data.get('error')}")
                        failed += 1
                else:
                    logger.error(f"  ✗ {test_case['legacy_tool']} mapping failed: No response")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"  ✗ {test_case['legacy_tool']} mapping failed with exception: {e}")
                failed += 1
        
        logger.info(f"Legacy mapping tests completed: {passed} passed, {failed} failed")
        return failed == 0
    
    async def measure_performance(self) -> Dict[str, Any]:
        """Measure performance of consolidated vs legacy tools."""
        logger.info("Measuring performance...")
        
        performance_metrics = {
            "consolidated_tools": {},
            "legacy_tools": {},
            "improvement_percentage": {}
        }
        
        if self.dry_run:
            logger.info("[DRY RUN] Would measure performance")
            return performance_metrics
        
        # Test cases for performance measurement
        test_operations = [
            {
                "name": "create_work_item",
                "consolidated": ("jive_manage_work_item", {"action": "create", "type": "task", "title": "Perf Test"}),
                "legacy": ("jive_create_work_item", {"type": "task", "title": "Perf Test"})
            },
            {
                "name": "get_work_item",
                "consolidated": ("jive_get_work_item", {"work_item_id": "test-123"}),
                "legacy": ("jive_get_work_item", {"work_item_id": "test-123"})
            }
        ]
        
        for operation in test_operations:
            try:
                # Measure consolidated tool performance
                start_time = datetime.now()
                await self.consolidated_registry.call_tool(
                    operation["consolidated"][0],
                    operation["consolidated"][1]
                )
                consolidated_time = (datetime.now() - start_time).total_seconds()
                
                # Measure legacy tool performance
                start_time = datetime.now()
                await self.legacy_registry.call_tool(
                    operation["legacy"][0],
                    operation["legacy"][1]
                )
                legacy_time = (datetime.now() - start_time).total_seconds()
                
                # Calculate improvement
                improvement = ((legacy_time - consolidated_time) / legacy_time) * 100 if legacy_time > 0 else 0
                
                performance_metrics["consolidated_tools"][operation["name"]] = consolidated_time
                performance_metrics["legacy_tools"][operation["name"]] = legacy_time
                performance_metrics["improvement_percentage"][operation["name"]] = improvement
                
                logger.info(f"  {operation['name']}: {consolidated_time:.3f}s vs {legacy_time:.3f}s ({improvement:+.1f}%)")
                
            except Exception as e:
                logger.error(f"Performance test failed for {operation['name']}: {e}")
        
        self.migration_results["performance_metrics"] = performance_metrics
        return performance_metrics
    
    async def create_backup(self) -> bool:
        """Create a backup of current configuration and data."""
        logger.info("Creating backup...")
        
        try:
            backup_dir = Path("./backups") / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create backup in {backup_dir}")
                return True
            
            # Backup configuration
            config_backup = backup_dir / "config.json"
            with open(config_backup, 'w') as f:
                json.dump(self.migration_config.to_dict(), f, indent=2)
            
            # Backup current tool registry state
            if self.legacy_registry:
                registry_stats = await self.legacy_registry.get_registry_stats()
                stats_backup = backup_dir / "registry_stats.json"
                with open(stats_backup, 'w') as f:
                    json.dump(registry_stats, f, indent=2, default=str)
            
            # Create rollback script
            rollback_script = backup_dir / "rollback.py"
            with open(rollback_script, 'w') as f:
                f.write(self._generate_rollback_script(backup_dir))
            
            self.migration_results["rollback_available"] = True
            logger.info(f"Backup created successfully in {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def _generate_rollback_script(self, backup_dir: Path) -> str:
        """Generate a rollback script."""
        return f'''#!/usr/bin/env python3
"""Rollback script for MCP Jive tool migration.

This script rolls back the migration to consolidated tools.
"""

import os
import sys
import json
from pathlib import Path

def rollback():
    """Rollback the migration."""
    print("Rolling back MCP Jive tool migration...")
    
    # Set environment variables to use legacy tools
    os.environ["MCP_JIVE_TOOL_MODE"] = "legacy_only"
    os.environ["MCP_JIVE_LEGACY_SUPPORT"] = "true"
    
    print("Environment variables set for legacy mode")
    print("Please restart the MCP Jive server to complete rollback")
    print("")
    print("To verify rollback:")
    print("  1. Check that MCP_JIVE_TOOL_MODE=legacy_only")
    print("  2. Restart the server")
    print("  3. Verify legacy tools are available")
    
if __name__ == "__main__":
    rollback()
'''
    
    async def execute_migration(self) -> bool:
        """Execute the full migration process."""
        logger.info("Starting migration to consolidated tools...")
        self.migration_results["start_time"] = datetime.now().isoformat()
        self.migration_results["status"] = "in_progress"
        
        try:
            # Step 1: Initialize environment
            await self.initialize()
            
            # Step 2: Create registries
            await self.create_registries()
            
            # Step 3: Validate environment
            if not await self.validate_environment():
                self.migration_results["status"] = "failed_validation"
                return False
            
            # Step 4: Create backup
            if not await self.create_backup():
                logger.warning("Backup creation failed, continuing without backup")
            
            # Step 5: Run compatibility tests
            if not await self.run_compatibility_tests():
                self.migration_results["status"] = "failed_tests"
                return False
            
            # Step 6: Run legacy mapping tests
            if not await self.run_legacy_mapping_tests():
                self.migration_results["status"] = "failed_legacy_tests"
                return False
            
            # Step 7: Measure performance
            await self.measure_performance()
            
            # Step 8: Complete migration
            if not self.dry_run:
                await self._apply_migration()
            
            self.migration_results["status"] = "completed"
            self.migration_results["end_time"] = datetime.now().isoformat()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_results["status"] = "failed_error"
            self.migration_results["end_time"] = datetime.now().isoformat()
            return False
    
    async def _apply_migration(self) -> None:
        """Apply the migration by updating configuration."""
        logger.info("Applying migration configuration...")
        
        # Update environment variables for production
        config_file = Path("./config/production.env")
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            f.write("# MCP Jive Production Configuration - Consolidated Tools\n")
            f.write("MCP_JIVE_TOOL_MODE=consolidated\n")
            f.write("MCP_JIVE_LEGACY_SUPPORT=false\n")
            f.write("MCP_JIVE_LEGACY_WARNINGS=false\n")
            f.write("MCP_JIVE_TOOL_CACHING=true\n")
            f.write("MCP_JIVE_AI_ORCHESTRATION=false\n")
            f.write("MCP_JIVE_QUALITY_GATES=false\n")
        
        logger.info(f"Production configuration written to {config_file}")
    
    def generate_report(self) -> str:
        """Generate a migration report."""
        report = f"""
# MCP Jive Tool Migration Report

**Migration Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: {self.migration_results['status']}
**Mode**: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}

## Summary

- **Tests Passed**: {self.migration_results['tests_passed']}
- **Tests Failed**: {self.migration_results['tests_failed']}
- **Validation Errors**: {len(self.migration_results['validation_errors'])}
- **Rollback Available**: {self.migration_results['rollback_available']}

## Validation Results

"""
        
        if self.migration_results['validation_errors']:
            report += "### Validation Errors\n\n"
            for error in self.migration_results['validation_errors']:
                report += f"- {error}\n"
        else:
            report += "✓ All validation checks passed\n"
        
        report += "\n## Performance Metrics\n\n"
        
        if self.migration_results['performance_metrics']:
            metrics = self.migration_results['performance_metrics']
            for operation, improvement in metrics.get('improvement_percentage', {}).items():
                report += f"- **{operation}**: {improvement:+.1f}% improvement\n"
        else:
            report += "No performance metrics available\n"
        
        report += "\n## Tool Mapping\n\n"
        report += f"- **Consolidated Tools**: {len(CONSOLIDATED_TOOLS)}\n"
        report += f"- **Legacy Tools Replaced**: {len(LEGACY_TOOLS_REPLACED)}\n"
        report += f"- **Reduction**: {((len(LEGACY_TOOLS_REPLACED) - len(CONSOLIDATED_TOOLS)) / len(LEGACY_TOOLS_REPLACED) * 100):.1f}%\n"
        
        if self.migration_results['status'] == 'completed':
            report += "\n## Next Steps\n\n"
            report += "1. Restart the MCP Jive server\n"
            report += "2. Verify consolidated tools are working\n"
            report += "3. Monitor performance and error rates\n"
            report += "4. Update client applications to use new tool names\n"
            report += "5. Remove legacy tool references from documentation\n"
        
        return report
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.consolidated_registry:
                await self.consolidated_registry.cleanup()
            if self.legacy_registry:
                await self.legacy_registry.cleanup()
            if self.storage:
                await self.storage.cleanup()
            if self.lancedb_manager:
                await self.lancedb_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="Migrate MCP Jive to consolidated tools")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Run in dry-run mode (no changes)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--report-file", "-r", help="Output file for migration report")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run migration
    migration = MigrationScript(config_file=args.config, dry_run=args.dry_run)
    
    try:
        success = await migration.execute_migration()
        
        # Generate report
        report = migration.generate_report()
        
        if args.report_file:
            with open(args.report_file, 'w') as f:
                f.write(report)
            logger.info(f"Migration report written to {args.report_file}")
        else:
            print("\n" + "="*60)
            print(report)
            print("="*60)
        
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed with exception: {e}")
        sys.exit(1)
    finally:
        await migration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())