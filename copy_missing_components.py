#!/usr/bin/env python3
"""
Copy missing components from mcp_server to mcp_jive.
"""

import os
import shutil
from pathlib import Path
from typing import List, Set

def get_directory_structure(path: Path) -> Set[str]:
    """Get all files and directories in a path."""
    items = set()
    if path.exists():
        for item in path.rglob('*'):
            if item.is_file():
                # Get relative path from the base directory
                rel_path = item.relative_to(path)
                items.add(str(rel_path))
    return items

def copy_missing_components():
    """Copy missing components from mcp_server to mcp_jive."""
    print("=== Copying Missing Components from MCP Server to MCP Jive ===")
    print()
    
    src_mcp_server = Path('src/mcp_server')
    src_mcp_jive = Path('src/mcp_jive')
    
    if not src_mcp_server.exists():
        print("❌ mcp_server directory not found")
        return
    
    if not src_mcp_jive.exists():
        print("❌ mcp_jive directory not found")
        return
    
    # Get existing files in both directories
    server_files = get_directory_structure(src_mcp_server)
    jive_files = get_directory_structure(src_mcp_jive)
    
    print(f"Files in mcp_server: {len(server_files)}")
    print(f"Files in mcp_jive: {len(jive_files)}")
    print()
    
    # Find missing files (in server but not in jive)
    missing_files = server_files - jive_files
    
    # Files to skip (already exist in mcp_jive or are duplicates)
    skip_files = {
        '__init__.py',  # Already exists
        'config.py',    # Already exists
        'database.py',  # Already exists
        'lancedb_manager.py',  # Already exists
        'server.py',    # Already exists
        'tools/__init__.py',  # Already exists
        'tools/registry.py',  # Already exists
    }
    
    # Filter out files we want to skip
    files_to_copy = [f for f in missing_files if f not in skip_files]
    
    print(f"Missing files to copy: {len(files_to_copy)}")
    
    if not files_to_copy:
        print("✓ No missing files to copy")
        return
    
    # Copy missing files
    copied_count = 0
    for file_path in sorted(files_to_copy):
        src_file = src_mcp_server / file_path
        dst_file = src_mcp_jive / file_path
        
        try:
            # Create parent directories if they don't exist
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(src_file, dst_file)
            print(f"✓ Copied: {file_path}")
            copied_count += 1
            
        except Exception as e:
            print(f"❌ Failed to copy {file_path}: {e}")
    
    print()
    print(f"=== Copy Summary ===")
    print(f"Files copied: {copied_count}/{len(files_to_copy)}")
    
    if copied_count > 0:
        print()
        print("Next steps:")
        print("1. Review copied files for any mcp_server internal imports")
        print("2. Update internal imports in copied files")
        print("3. Run import consolidation script")
        print("4. Test the application")

def update_internal_imports_in_copied_files():
    """Update internal imports in copied files from mcp_server to mcp_jive."""
    print("\n=== Updating Internal Imports in Copied Files ===")
    print()
    
    src_mcp_jive = Path('src/mcp_jive')
    
    # Find all Python files in mcp_jive
    python_files = list(src_mcp_jive.rglob('*.py'))
    
    updated_count = 0
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace internal mcp_server imports with mcp_jive
            content = content.replace('from mcp_server.', 'from mcp_jive.')
            content = content.replace('import mcp_server.', 'import mcp_jive.')
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Updated internal imports: {file_path.relative_to(src_mcp_jive)}")
                updated_count += 1
                
        except Exception as e:
            print(f"❌ Failed to update {file_path}: {e}")
    
    print(f"\nUpdated internal imports in {updated_count} files")

if __name__ == "__main__":
    copy_missing_components()
    update_internal_imports_in_copied_files()