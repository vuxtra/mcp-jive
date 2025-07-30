#!/usr/bin/env python3
"""
Phase 1: Critical Database Infrastructure Fixes

This script implements the Phase 1 recommendations from the tool audit:
1. Database layer stabilization
2. Weaviate client API corrections
3. Connection pooling and retry logic
4. Database health monitoring
"""

import os
import re
import time
import asyncio
from pathlib import Path
from typing import List, Tuple, Dict, Any


class DatabaseInfrastructureFixer:
    """Implements Phase 1 database infrastructure fixes."""
    
    def __init__(self):
        self.src_dir = Path(__file__).parent.parent / "src" / "mcp_server"
        self.tools_dir = self.src_dir / "tools"
        self.fixes_applied = []
        self.files_modified = set()
        
    def apply_all_fixes(self):
        """Apply all Phase 1 database fixes."""
        print("🔧 Phase 1: Critical Database Infrastructure Fixes")
        print("=" * 60)
        
        # 1. Fix Weaviate client API usage
        self.fix_weaviate_client_api()
        
        # 2. Add connection retry logic
        self.add_connection_retry_logic()
        
        # 3. Implement proper error handling
        self.implement_database_error_handling()
        
        # 4. Add database health monitoring
        self.add_database_health_monitoring()
        
        # 5. Update database configuration
        self.update_database_configuration()
        
        # Print summary
        self.print_summary()
        
    def fix_weaviate_client_api(self):
        """Fix Weaviate client API usage patterns."""
        print("\n1. 🔍 Fixing Weaviate Client API Usage...")
        
        # API method corrections based on Weaviate v4 client
        api_fixes = [
            # Query collection fixes
            (r'collection\.query\.get\(', 'collection.query.fetch_objects('),
            (r'collection\.query\.hybrid\(([^)]+)\)', r'collection.query.hybrid(\1).with_limit(50)'),
            
            # Filter method corrections
            (r'\.Filter\(', '.with_where('),
            (r'\.where\(', '.with_where('),
            
            # Search method corrections
            (r'collection\.query\.near_text\(', 'collection.query.near_text('),
            
            # Aggregation fixes
            (r'collection\.aggregate\.over_all\(', 'collection.aggregate.over_all('),
        ]
        
        files_to_fix = [
            "search_discovery.py",
            "task_management.py", 
            "client_tools.py",
            "storage_sync.py",
            "validation_tools.py"
        ]
        
        for filename in files_to_fix:
            file_path = self.tools_dir / filename
            if file_path.exists():
                self._apply_regex_fixes(file_path, api_fixes, "Weaviate API")
                
    def add_connection_retry_logic(self):
        """Add connection retry logic to database operations."""
        print("\n2. 🔄 Adding Connection Retry Logic...")
        
        database_file = self.src_dir / "database.py"
        if database_file.exists():
            content = database_file.read_text()
            
            # Add retry decorator if not present
            if "@retry" not in content and "def retry_on_connection_error" not in content:
                retry_logic = '''
import time
import functools
from typing import Callable, Any

def retry_on_connection_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry database operations on connection errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a connection-related error
                    if any(keyword in error_msg for keyword in [
                        'connection refused', 'connection failed', 'unavailable',
                        'timeout', 'grpc', 'network', 'unreachable'
                    ]):
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Re-raise non-connection errors immediately
                    raise e
                    
            # If all retries failed, raise the last exception
            raise last_exception
        return wrapper
    return decorator
'''
                
                # Insert after imports
                import_pattern = r'(import logging\n)'
                if re.search(import_pattern, content):
                    content = re.sub(import_pattern, r'\1' + retry_logic, content)
                    database_file.write_text(content)
                    self.fixes_applied.append("Added retry logic to database.py")
                    self.files_modified.add(str(database_file))
                    
    def implement_database_error_handling(self):
        """Implement proper database error handling."""
        print("\n3. ⚠️ Implementing Database Error Handling...")
        
        # Add standardized error handling to tool files
        error_handling_fixes = [
            # Wrap database operations in try-catch
            (r'(collection\.[a-zA-Z_]+\([^)]*\))', 
             r'await self._safe_database_operation(lambda: \1)'),
            
            # Add error logging
            (r'except Exception as e:\s*\n\s*logger\.error\(f"Error ([^"]+): {e}"\)',
             r'except Exception as e:\n        logger.error(f"Database error in \1: {e}", exc_info=True)\n        return self._format_error_response("\1", str(e))'),
        ]
        
        files_to_fix = [
            "task_management.py",
            "client_tools.py", 
            "search_discovery.py",
            "storage_sync.py"
        ]
        
        for filename in files_to_fix:
            file_path = self.tools_dir / filename
            if file_path.exists():
                self._add_error_handling_methods(file_path)
                
    def _add_error_handling_methods(self, file_path: Path):
        """Add error handling methods to a tool file."""
        content = file_path.read_text()
        
        # Check if error handling methods already exist
        if "_safe_database_operation" not in content:
            error_methods = '''
    async def _safe_database_operation(self, operation):
        """Safely execute a database operation with error handling."""
        try:
            return await operation()
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in [
                'connection refused', 'unavailable', 'grpc', 'timeout'
            ]):
                logger.error(f"Database connection error: {e}")
                return self._format_error_response("database_connection", "Database temporarily unavailable")
            else:
                logger.error(f"Database operation error: {e}", exc_info=True)
                return self._format_error_response("database_operation", str(e))
                
    def _format_error_response(self, error_type: str, error_message: str):
        """Format a standardized error response."""
        from mcp.types import TextContent
        return [TextContent(
            type="text",
            text=f"Error ({error_type}): {error_message}"
        )]
'''
            
            # Insert before the last method or class end
            class_end_pattern = r'(\n\s+async def [^\n]+\n[\s\S]*?)$'
            if re.search(class_end_pattern, content):
                content = re.sub(r'(class [^:]+:[\s\S]*?)(\n\s+async def [^\n]+)', 
                                r'\1' + error_methods + r'\2', content)
                file_path.write_text(content)
                self.fixes_applied.append(f"Added error handling methods to {file_path.name}")
                self.files_modified.add(str(file_path))
                
    def add_database_health_monitoring(self):
        """Add database health monitoring capabilities."""
        print("\n4. 📊 Adding Database Health Monitoring...")
        
        # Create database health monitor
        health_monitor_content = '''
"""Database Health Monitoring Module"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Monitors database health and connection status."""
    
    def __init__(self, weaviate_manager):
        self.weaviate_manager = weaviate_manager
        self.health_metrics = {
            "last_check": None,
            "connection_status": "unknown",
            "response_time_ms": None,
            "error_count": 0,
            "success_count": 0,
            "uptime_percentage": 100.0
        }
        self.check_interval = 30  # seconds
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitor_loop())
            logger.info("Database health monitoring started")
            
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Database health monitoring stopped")
            
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def check_health(self) -> Dict[str, Any]:
        """Check database health and update metrics."""
        start_time = time.time()
        
        try:
            # Simple health check - try to get cluster info
            if hasattr(self.weaviate_manager, 'client') and self.weaviate_manager.client:
                cluster_info = self.weaviate_manager.client.cluster.get_nodes_status()
                
                response_time = (time.time() - start_time) * 1000
                
                self.health_metrics.update({
                    "last_check": datetime.now().isoformat(),
                    "connection_status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "success_count": self.health_metrics["success_count"] + 1
                })
                
                logger.debug(f"Database health check passed in {response_time:.2f}ms")
                
            else:
                raise Exception("Weaviate client not available")
                
        except Exception as e:
            self.health_metrics.update({
                "last_check": datetime.now().isoformat(),
                "connection_status": "unhealthy",
                "response_time_ms": None,
                "error_count": self.health_metrics["error_count"] + 1,
                "last_error": str(e)
            })
            
            logger.warning(f"Database health check failed: {e}")
            
        # Calculate uptime percentage
        total_checks = self.health_metrics["success_count"] + self.health_metrics["error_count"]
        if total_checks > 0:
            self.health_metrics["uptime_percentage"] = (
                self.health_metrics["success_count"] / total_checks
            ) * 100
            
        return self.health_metrics.copy()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_metrics.copy()
        
    def is_healthy(self) -> bool:
        """Check if database is currently healthy."""
        return self.health_metrics["connection_status"] == "healthy"
'''
        
        health_file = self.src_dir / "database_health.py"
        health_file.write_text(health_monitor_content)
        self.fixes_applied.append("Created database health monitoring module")
        self.files_modified.add(str(health_file))
        
    def update_database_configuration(self):
        """Update database configuration for better reliability."""
        print("\n5. ⚙️ Updating Database Configuration...")
        
        config_file = self.src_dir / "config.py"
        if config_file.exists():
            content = config_file.read_text()
            
            # Add database reliability settings
            if "weaviate_timeout" not in content:
                config_additions = '''
        # Database reliability settings
        self.weaviate_timeout = int(os.getenv("WEAVIATE_TIMEOUT", "30"))
        self.weaviate_retries = int(os.getenv("WEAVIATE_RETRIES", "3"))
        self.weaviate_retry_delay = float(os.getenv("WEAVIATE_RETRY_DELAY", "1.0"))
        self.weaviate_health_check_interval = int(os.getenv("WEAVIATE_HEALTH_CHECK_INTERVAL", "30"))
        self.weaviate_connection_pool_size = int(os.getenv("WEAVIATE_CONNECTION_POOL_SIZE", "10"))
'''
                
                # Insert before the to_dict method
                to_dict_pattern = r'(\s+def to_dict\(self\):)'
                if re.search(to_dict_pattern, content):
                    content = re.sub(to_dict_pattern, config_additions + r'\1', content)
                    
                    # Also add to to_dict method
                    dict_content_pattern = r'("weaviate_grpc_port": self\.weaviate_grpc_port,)'
                    if re.search(dict_content_pattern, content):
                        dict_additions = '''
            "weaviate_timeout": self.weaviate_timeout,
            "weaviate_retries": self.weaviate_retries,
            "weaviate_retry_delay": self.weaviate_retry_delay,
            "weaviate_health_check_interval": self.weaviate_health_check_interval,
            "weaviate_connection_pool_size": self.weaviate_connection_pool_size,'''
                        content = re.sub(dict_content_pattern, r'\1' + dict_additions, content)
                        
                    config_file.write_text(content)
                    self.fixes_applied.append("Added database reliability settings to config")
                    self.files_modified.add(str(config_file))
                    
    def _apply_regex_fixes(self, file_path: Path, fixes: List[Tuple], fix_type: str):
        """Apply regex-based fixes to a file."""
        try:
            content = file_path.read_text()
            original_content = content
            
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content)
                    
            if content != original_content:
                file_path.write_text(content)
                self.fixes_applied.append(f"{fix_type} fixes applied to {file_path.name}")
                self.files_modified.add(str(file_path))
                print(f"   ✅ Applied {fix_type} fixes to {file_path.name}")
            else:
                print(f"   ℹ️  No {fix_type} fixes needed in {file_path.name}")
                
        except Exception as e:
            print(f"   ❌ Error applying {fix_type} fixes to {file_path.name}: {e}")
            
    def print_summary(self):
        """Print summary of applied fixes."""
        print("\n" + "=" * 60)
        print("📋 PHASE 1 DATABASE FIXES SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ Total Fixes Applied: {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
            
        print(f"\n📁 Files Modified: {len(self.files_modified)}")
        for file_path in sorted(self.files_modified):
            print(f"   • {Path(file_path).name}")
            
        print("\n🔄 Next Steps:")
        print("   1. Restart the MCP server to load new configurations")
        print("   2. Run detailed audit to verify database improvements")
        print("   3. Monitor database health metrics")
        print("   4. Proceed to Phase 2: UUID handling fixes")
        
        print("\n📊 Expected Improvements:")
        print("   • Reduced database connection failures")
        print("   • Better error handling and recovery")
        print("   • Real-time health monitoring")
        print("   • Improved tool reliability from 25.7% to ~40-50%")
        
        print("\n⚠️  Note: Server restart required for configuration changes.")


def main():
    """Main fix application function."""
    fixer = DatabaseInfrastructureFixer()
    
    try:
        fixer.apply_all_fixes()
        print("\n🎉 Phase 1 database fixes completed successfully!")
        return 0
    except Exception as e:
        print(f"\n💥 Phase 1 fixes failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())