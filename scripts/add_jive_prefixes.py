#!/usr/bin/env python3
"""
Script to add 'jive_' prefixes to all MCP tools and enhance descriptions
with agile workflow keywords (Initiative, Epic, Feature, Story, Task).

This addresses tool name collision concerns and improves context triggers.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Tool files to update
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

# Agile workflow keywords to enhance descriptions
AGILE_KEYWORDS = {
    "initiative": "high-level business initiative",
    "epic": "large epic spanning multiple features", 
    "feature": "product feature or capability",
    "story": "user story or requirement",
    "task": "development task or work item"
}

def add_jive_prefix_to_tool_name(content: str) -> str:
    """
    Add 'jive_' prefix to tool names in Tool() definitions.
    """
    # Pattern to match Tool name definitions
    pattern = r'name="([^"]+)"'
    
    def replace_name(match):
        tool_name = match.group(1)
        if not tool_name.startswith('jive_'):
            return f'name="jive_{tool_name}"'
        return match.group(0)
    
    return re.sub(pattern, replace_name, content)

def enhance_tool_descriptions(content: str) -> str:
    """
    Enhance tool descriptions with Jive and agile workflow keywords.
    """
    # Pattern to match description fields
    pattern = r'description="([^"]+)"'
    
    def enhance_description(match):
        desc = match.group(1)
        
        # Add Jive context if not present
        if 'jive' not in desc.lower():
            desc = f"Jive: {desc}"
        
        # Enhance with agile keywords where relevant
        for keyword, enhancement in AGILE_KEYWORDS.items():
            if keyword in desc.lower() and enhancement not in desc.lower():
                desc = desc.replace(keyword, f"{keyword} ({enhancement})")
        
        return f'description="{desc}"'
    
    return re.sub(pattern, enhance_description, content)

def update_tool_handlers(content: str) -> str:
    """
    Update tool handler method calls to use jive_ prefixed names.
    """
    # Pattern to match tool handler calls
    patterns = [
        (r'if name == "([^"]+)":', r'if name == "jive_\1":'),
        (r'elif name == "([^"]+)":', r'elif name == "jive_\1":'),
        (r'case "([^"]+)":', r'case "jive_\1":'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(file_path: str) -> Tuple[bool, str]:
    """
    Process a single tool file to add jive_ prefixes and enhance descriptions.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply transformations
        content = original_content
        content = add_jive_prefix_to_tool_name(content)
        content = enhance_tool_descriptions(content)
        content = update_tool_handlers(content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Updated {file_path}"
        else:
            return True, f"No changes needed for {file_path}"
            
    except Exception as e:
        return False, f"Error processing {file_path}: {str(e)}"

def main():
    """
    Main function to process all tool files.
    """
    print("Adding 'jive_' prefixes to MCP tools...")
    print("This will help prevent tool name collisions and improve context triggers.")
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
        print("\n✅ All tool files updated successfully!")
        print("\nNext steps:")
        print("1. Update README.md with new tool names")
        print("2. Update any documentation referencing old tool names")
        print("3. Test the server to ensure all tools work correctly")
    else:
        print("\n❌ Some files had errors. Please review and fix manually.")

if __name__ == "__main__":
    main()