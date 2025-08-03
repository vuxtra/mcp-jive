#!/usr/bin/env python3
"""
Consolidate imports from mcp_server to mcp_jive across the codebase.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Define import mappings from mcp_server to mcp_jive
IMPORT_MAPPINGS = {
    # Core components
    'from mcp_jive.server import MCPServer': 'from mcp_jive.server import MCPServer',
    'from mcp_jive.config import ServerConfig': 'from mcp_jive.config import ServerConfig',
    'from mcp_jive.lancedb_manager import LanceDBManager': 'from mcp_jive.lancedb_manager import LanceDBManager',
    'from mcp_jive.lancedb_manager import DatabaseConfig': 'from mcp_jive.lancedb_manager import DatabaseConfig',
    'from mcp_jive.lancedb_manager import SearchType': 'from mcp_jive.lancedb_manager import SearchType',
    
    # Combined imports
    'from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig': 'from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig',
    'from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType': 'from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType',
    
    # Tools and other components
    'from mcp_jive.tools.client_tools import MCPClientTools': 'from mcp_jive.tools.client_tools import MCPClientTools',
    'from mcp_jive.tools.registry import MCPToolRegistry': 'from mcp_jive.tools.registry import MCPToolRegistry',
    'from mcp_jive.tools.task_management import TaskManagementTools': 'from mcp_jive.tools.task_management import TaskManagementTools',
    'from mcp_jive.tools.workflow_engine import WorkflowEngineTools': 'from mcp_jive.tools.workflow_engine import WorkflowEngineTools',
    
    # Health and monitoring
    'from mcp_jive.health import HealthMonitor': 'from mcp_jive.health import HealthMonitor',
    
    # Models
    'from mcp_jive.models.workflow import WorkItem': 'from mcp_jive.models.workflow import WorkItem',
    'from mcp_jive.models.workflow import WorkItemType': 'from mcp_jive.models.workflow import WorkItemType',
    'from mcp_jive.models.workflow import WorkItemStatus': 'from mcp_jive.models.workflow import WorkItemStatus',
    'from mcp_jive.models.workflow import Priority': 'from mcp_jive.models.workflow import Priority',
    
    # Services
    'from mcp_jive.services.sync_engine import SyncResult': 'from mcp_jive.services.sync_engine import SyncResult',
    'from mcp_jive.services.sync_engine import SyncStatus': 'from mcp_jive.services.sync_engine import SyncStatus',
    
    # Utils
    'from mcp_jive.utils.identifier_resolver import IdentifierResolver': 'from mcp_jive.utils.identifier_resolver import IdentifierResolver',
    
    # Database (legacy Weaviate references)
    'from mcp_jive.lancedb_manager import LanceDBManager  # Migrated from Weaviate': 'from mcp_jive.lancedb_manager import LanceDBManager  # Migrated from Weaviate',
}

# Files to exclude from automatic conversion (need manual review)
EXCLUDE_FILES = {
    'migrate_data.py',  # Migration script - keep as is
    'analyze_databases.py',  # Analysis script - keep as is
    'simple_db_check.py',  # Comparison script - keep as is
    'compare_databases.py',  # Comparison script - keep as is
    'debug_database_mismatch.py',  # Debug script - keep as is
}

# Directories to exclude
EXCLUDE_DIRS = {
    'backups',
    '.git',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
}

def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    
    for file_path in root_dir.rglob('*.py'):
        # Skip excluded directories
        if any(exclude_dir in file_path.parts for exclude_dir in EXCLUDE_DIRS):
            continue
            
        # Skip excluded files
        if file_path.name in EXCLUDE_FILES:
            continue
            
        python_files.append(file_path)
    
    return python_files

def update_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Apply import mappings
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_made.append(f"  {old_import} → {new_import}")
        
        # Handle generic mcp_server imports that might not be in our mapping
        # Look for patterns like "import mcp_jive.something"
        generic_patterns = [
            (r'import mcp_server\.([\w\.]+)', r'import mcp_jive.\1'),
            (r'from mcp_server\.([\w\.]+) import', r'from mcp_jive.\1 import'),
        ]
        
        for pattern, replacement in generic_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                for match in matches:
                    changes_made.append(f"  Generic: mcp_server.{match} → mcp_jive.{match}")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        
        return False, []
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, []

def main():
    """Main consolidation function."""
    print("=== MCP Server to MCP Jive Import Consolidation ===")
    print()
    
    root_dir = Path('.')
    python_files = find_python_files(root_dir)
    
    print(f"Found {len(python_files)} Python files to process")
    print()
    
    total_files_changed = 0
    total_changes = 0
    
    for file_path in python_files:
        changed, changes = update_imports_in_file(file_path)
        
        if changed:
            total_files_changed += 1
            total_changes += len(changes)
            print(f"✓ Updated {file_path}:")
            for change in changes:
                print(change)
            print()
    
    print("=== Consolidation Summary ===")
    print(f"Files processed: {len(python_files)}")
    print(f"Files changed: {total_files_changed}")
    print(f"Total import changes: {total_changes}")
    print()
    
    if total_files_changed > 0:
        print("Next steps:")
        print("1. Review the changes made")
        print("2. Test the application to ensure everything works")
        print("3. Remove the mcp_server directory after verification")
        print("4. Update any remaining references in documentation")
    else:
        print("No import changes were needed.")

if __name__ == "__main__":
    main()