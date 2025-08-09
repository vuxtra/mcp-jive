#!/usr/bin/env python3
"""
Script to remove extra closing braces that were introduced during syntax fixes
"""

import re
import os

def remove_extra_braces():
    file_path = "src/mcp_jive/tools/consolidated/unified_hierarchy_tool.py"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines[:]
    fixes_applied = 0
    
    # Find lines that are just whitespace + }
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "}":
            # Check if this is a standalone closing brace that shouldn't be there
            # Look at the previous line to see if it ends with a function call
            if i > 0:
                prev_line = lines[i-1].strip()
                if (prev_line.endswith('")') or 
                    prev_line.endswith('error_code="') or
                    'ErrorHandler.create_error_response' in prev_line):
                    # This is likely an extra brace, remove it
                    lines[i] = ""
                    fixes_applied += 1
                    print(f"Removed extra brace at line {i+1}: {line.strip()}")
    
    if fixes_applied > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"\n✅ Removed {fixes_applied} extra braces from {file_path}")
    else:
        print(f"\n✅ No extra braces found in {file_path}")

if __name__ == "__main__":
    remove_extra_braces()