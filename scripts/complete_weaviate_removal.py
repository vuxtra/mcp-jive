#!/usr/bin/env python3
"""
Complete Weaviate Dependency Removal Script

This script systematically removes all remaining Weaviate dependencies
and replaces them with LanceDB equivalents.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def update_file_content(file_path: Path, replacements: List[Tuple[str, str]]) -> bool:
    """Update file content with given replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_pattern, new_pattern in replacements:
            content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to remove Weaviate dependencies."""
    print("🔄 Starting complete Weaviate dependency removal...")
    
    # Define base directory
    base_dir = Path(__file__).parent.parent / "src"
    
    # Common replacements for all files
    common_replacements = [
        # Import replacements
        (r'from \.\.(database|lancedb_manager) import WeaviateManager', r'from ..lancedb_manager import LanceDBManager'),
        (r'from \.(database|lancedb_manager) import WeaviateManager', r'from .lancedb_manager import LanceDBManager'),
        
        # Constructor parameter replacements
        (r'weaviate_manager: WeaviateManager', r'lancedb_manager: LanceDBManager'),
        (r'self\.weaviate_manager = weaviate_manager', r'self.lancedb_manager = lancedb_manager'),
        
        # Method call replacements
        (r'self\.weaviate_manager', r'self.lancedb_manager'),
        (r'weaviate_manager', r'lancedb_manager'),
        
        # Collection method replacements
        (r'\.get_collection\(', r'.db.open_table('),
        
        # Comment updates
        (r'Weaviate database', r'LanceDB database'),
        (r'weaviate database', r'LanceDB database'),
        (r'embedded Weaviate', r'embedded LanceDB'),
        (r'Embedded Weaviate', r'Embedded LanceDB'),
    ]
    
    # Files to update with common replacements
    files_to_update = [
        "mcp_server/services/sync_engine.py",
        "mcp_server/tools/client_tools.py", 
        "mcp_server/utils/identifier_resolver.py",
        "mcp_server/tools/storage_sync.py",
        "mcp_server/services/hierarchy_manager.py",
        "mcp_server/tools/search_discovery.py",
        "mcp_server/tools/workflow_execution.py",
        "mcp_server/services/autonomous_executor.py",
        "mcp_server/tools/task_management.py",
        "mcp_server/tools/progress_tracking.py",
        "mcp_server/database_health.py",
    ]
    
    updated_count = 0
    
    # Update files with common replacements
    for file_path in files_to_update:
        full_path = base_dir / file_path
        if full_path.exists():
            if update_file_content(full_path, common_replacements):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {full_path}")
    
    # Special handling for specific files
    
    # Update main.py - remove Weaviate references in comments
    main_py_replacements = [
        (r'WEAVIATE_HOST.*# Weaviate host.*', r'# Legacy Weaviate configuration (deprecated)'),
        (r'WEAVIATE_PORT.*# Weaviate port.*', r'# Legacy Weaviate configuration (deprecated)'),
        (r'help="Initialize the Weaviate database and exit"', r'help="Initialize the database and exit"'),
        (r'await weaviate_manager\.stop\(\)', r'# Legacy cleanup - now handled by LanceDB'),
    ]
    
    main_py_path = base_dir / "main.py"
    if main_py_path.exists():
        if update_file_content(main_py_path, main_py_replacements):
            updated_count += 1
    
    # Update server.py - remove Weaviate URL reference
    server_py_replacements = [
        (r'"weaviate_url": self\.config\.weaviate_url,', r'"database_type": "lancedb",'),
    ]
    
    server_py_path = base_dir / "mcp_server/server.py"
    if server_py_path.exists():
        if update_file_content(server_py_path, server_py_replacements):
            updated_count += 1
    
    # Update config files - mark Weaviate configs as deprecated
    config_replacements = [
        (r'"""Weaviate database configuration\."""', r'"""Legacy Weaviate configuration (deprecated)."""'),
        (r'# Weaviate Configuration', r'# Legacy Weaviate Configuration (deprecated)'),
        (r'def weaviate_url', r'def legacy_weaviate_url'),
        (r'def weaviate_grpc_url', r'def legacy_weaviate_grpc_url'),
    ]
    
    config_files = [
        "mcp_server/config.py",
        "mcp_jive/config.py",
    ]
    
    for config_file in config_files:
        config_path = base_dir / config_file
        if config_path.exists():
            if update_file_content(config_path, config_replacements):
                updated_count += 1
    
    # Update circuit_breaker.py
    circuit_breaker_replacements = [
        (r'WEAVIATE_CIRCUIT_BREAKER', r'DATABASE_CIRCUIT_BREAKER'),
    ]
    
    circuit_breaker_path = base_dir / "mcp_server/circuit_breaker.py"
    if circuit_breaker_path.exists():
        if update_file_content(circuit_breaker_path, circuit_breaker_replacements):
            updated_count += 1
    
    # Update workflow_engine.py - fix remaining Weaviate collection calls
    workflow_engine_replacements = [
        (r'collection = self\.weaviate_manager\.get_collection\("WorkItem"\)', 
         r'table = self.lancedb_manager.db.open_table("WorkItem")'),
        (r'# Check if collection exists, if not it will be created by WeaviateManager',
         r'# Check if table exists, if not it will be created by LanceDBManager'),
        (r'# Query Weaviate for work items', r'# Query LanceDB for work items'),
        (r'collection = self\.weaviate_manager\.get_collection\("WorkItem"\)',
         r'table = self.lancedb_manager.db.open_table("WorkItem")'),
    ]
    
    workflow_engine_path = base_dir / "mcp_server/tools/workflow_engine.py"
    if workflow_engine_path.exists():
        if update_file_content(workflow_engine_path, workflow_engine_replacements):
            updated_count += 1
    
    print(f"\n🎉 Weaviate dependency removal completed!")
    print(f"📊 Updated {updated_count} files")
    print(f"\n📝 Next steps:")
    print(f"  1. Run validation script to ensure everything works")
    print(f"  2. Remove Weaviate packages from requirements if present")
    print(f"  3. Update documentation to reflect LanceDB usage")

if __name__ == "__main__":
    main()