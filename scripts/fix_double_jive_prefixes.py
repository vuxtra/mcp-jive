#!/usr/bin/env python3
"""
Script to fix double jive_ prefixes in tool handler methods.
This fixes the issue where jive_ was added twice to some tool names.
"""

import os
import re
from typing import List, Tuple

# Tool files to fix
TOOL_FILES = [
    "src/mcp_server/tools/task_management.py",
    "src/mcp_server/tools/workflow_engine.py", 
    "src/mcp_server/tools/client_tools.py",
    "src/mcp_server/tools/search_discovery.py",
    "src/mcp_server/tools/progress_tracking.py",
    "src/mcp_server/tools/storage_sync.py",
    "src/mcp_server/tools/validation_tools.py",
    "src/mcp_server/tools/workflow_execution.py"
]

def fix_double_jive_prefixes(content: str) -> str:
    """
    Fix double jive_ prefixes in tool handler methods.
    """
    # Pattern to match double jive_ prefixes in handler methods
    patterns = [
        (r'name == "jive_jive_([^"]+)"', r'name == "jive_\1"'),
        (r'elif name == "jive_jive_([^"]+)"', r'elif name == "jive_\1"'),
        (r'case "jive_jive_([^"]+)"', r'case "jive_\1"'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(file_path: str) -> Tuple[bool, str]:
    """
    Process a single tool file to fix double jive_ prefixes.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply fix
        content = fix_double_jive_prefixes(original_content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Fixed double prefixes in {file_path}"
        else:
            return True, f"No double prefixes found in {file_path}"
            
    except Exception as e:
        return False, f"Error processing {file_path}: {str(e)}"

def main():
    """
    Main function to fix double jive_ prefixes in all tool files.
    """
    print("Fixing double jive_ prefixes in tool handler methods...")
    print()
    
    success_count = 0
    error_count = 0
    
    for file_path in TOOL_FILES:
        if os.path.exists(file_path):
            success, message = process_file(file_path)
            print(message)
            
            if success:
                success_count += 1
            else:
                error_count += 1
        else:
            print(f"Warning: File not found: {file_path}")
            error_count += 1
    
    print()
    print(f"Summary: {success_count} files processed successfully, {error_count} errors")
    
    if error_count == 0:
        print("\n✅ All double jive_ prefixes fixed successfully!")
    else:
        print("\n❌ Some files had errors. Please review and fix manually.")

if __name__ == "__main__":
    main()