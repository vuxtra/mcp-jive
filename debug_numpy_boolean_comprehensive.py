#!/usr/bin/env python3
"""
Simplified NumPy Boolean Evaluation Error Debugger

This script identifies the source of:
"ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()"

Based on research findings, this error occurs when:
1. NumPy arrays are used in boolean contexts (if statements, and/or operators)
2. Implicit boolean conversion happens during comparisons
3. Arrays are passed to functions expecting single boolean values
"""

import sys
import os
import traceback
import numpy as np
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.config import ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.tools.task_management import TaskManagementTools

def analyze_numpy_arrays_in_data(data, path="root"):
    """
    Recursively analyze data structures for NumPy arrays that might cause boolean evaluation errors.
    """
    issues = []
    
    if isinstance(data, np.ndarray):
        if data.size > 1:
            issues.append({
                'path': path,
                'type': 'numpy_array',
                'shape': data.shape,
                'dtype': data.dtype,
                'size': data.size,
                'content': str(data)[:100] + ('...' if len(str(data)) > 100 else ''),
                'risk': 'HIGH - Multi-element array could cause boolean evaluation error'
            })
        elif data.size == 1:
            issues.append({
                'path': path,
                'type': 'numpy_scalar',
                'shape': data.shape,
                'dtype': data.dtype,
                'size': data.size,
                'content': str(data),
                'risk': 'LOW - Single element array'
            })
    elif isinstance(data, dict):
        for key, value in data.items():
            issues.extend(analyze_numpy_arrays_in_data(value, f"{path}.{key}"))
    elif isinstance(data, (list, tuple)):
        for i, item in enumerate(data):
            issues.extend(analyze_numpy_arrays_in_data(item, f"{path}[{i}]"))
    
    return issues

def safe_task_update_with_analysis():
    """
    Attempt task update with detailed analysis of data at each step.
    """
    print("\n🔍 DETAILED TASK UPDATE ANALYSIS:")
    print("="*60)
    
    try:
        # Step 1: Initialize components
        print("\n📋 Step 1: Initializing components...")
        server_config = ServerConfig()
        db_config = DatabaseConfig()
        manager = LanceDBManager(db_config)
        task_tools = TaskManagementTools(server_config, manager)
        print("✅ Components initialized successfully")
        
        # Step 2: Prepare update data
        print("\n📋 Step 2: Preparing update data...")
        task_id = "c64b39b3-eb4c-44df-84f8-f3b38b7035a9"
        update_data = {
            "task_id": task_id,
            "status": "completed",
            "tags": ["debugging", "numpy-fix", "completed"]
        }
        
        print(f"Update data: {update_data}")
        
        # Analyze update data for NumPy arrays
        issues = analyze_numpy_arrays_in_data(update_data, "update_data")
        if issues:
            print(f"\n⚠️  Found {len(issues)} potential NumPy array issues in update data:")
            for issue in issues:
                print(f"   - {issue['path']}: {issue['risk']}")
                print(f"     Shape: {issue['shape']}, Type: {issue['dtype']}")
        else:
            print("✅ No NumPy arrays found in update data")
        
        # Step 3: Attempt the update with detailed error catching
        print(f"\n📋 Step 3: Attempting task update...")
        print(f"   Task ID: {task_id}")
        print(f"   Status: completed")
        print(f"   Tags: {update_data['tags']}")
        
        # Wrap the call in a try-catch to get the exact line where it fails
        try:
            # Use the correct method name (it's _update_task, not update_task)
            import asyncio
            result = asyncio.run(task_tools._update_task(update_data))
            print(f"\n✅ SUCCESS! Task update completed")
            print(f"Result: {result}")
            return result
            
        except ValueError as ve:
            if "ambiguous" in str(ve).lower():
                print(f"\n❌ FOUND THE NUMPY BOOLEAN ERROR!")
                print(f"Error message: {ve}")
                print(f"\n📍 DETAILED TRACEBACK:")
                print("-" * 60)
                
                # Get the full traceback
                tb = traceback.format_exc()
                print(tb)
                
                # Try to identify the specific line causing the issue
                print(f"\n🔍 ANALYZING TRACEBACK FOR NUMPY OPERATIONS:")
                lines = tb.split('\n')
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in ['numpy', 'array', 'bool', 'truth', 'ambiguous']):
                        print(f"   Line {i}: {line.strip()}")
                
                return None
            else:
                print(f"\n❌ Different ValueError: {ve}")
                traceback.print_exc()
                return None
                
    except Exception as e:
        print(f"\n❌ Unexpected error during analysis: {e}")
        traceback.print_exc()
        return None

def test_specific_numpy_patterns():
    """
    Test specific patterns that commonly cause the boolean evaluation error.
    """
    print("\n🧪 TESTING SPECIFIC NUMPY PATTERNS:")
    print("="*50)
    
    # Pattern 1: Array comparison in if statement
    print("\n1. Array comparison in if statement:")
    try:
        arr1 = np.array([1, 2, 3])
        arr2 = np.array([1, 2, 3])
        comparison = arr1 == arr2
        print(f"   Comparison result: {comparison}")
        print(f"   Type: {type(comparison)}")
        
        # This would cause the error:
        # if comparison:  # DON'T DO THIS
        #     print("Arrays are equal")
        
        # Correct ways:
        if comparison.all():
            print("   ✅ Using .all(): All elements match")
        if comparison.any():
            print("   ✅ Using .any(): Some elements match")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Pattern 2: Array in boolean context with get() method
    print("\n2. Array with get() method (common in our codebase):")
    try:
        data = {
            'tags': np.array(['tag1', 'tag2', 'tag3'])
        }
        
        # This pattern might cause issues:
        tags = data.get('tags')
        print(f"   Retrieved tags: {tags}")
        print(f"   Type: {type(tags)}")
        
        # Safe way to check if tags exist and have content:
        if tags is not None and (not isinstance(tags, np.ndarray) or tags.size > 0):
            print(f"   ✅ Safe check: Tags exist and have content")
        
        # Convert to Python list for safety:
        if isinstance(tags, np.ndarray):
            tags_list = tags.tolist()
            print(f"   ✅ Converted to list: {tags_list}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Pattern 3: Metadata comparison
    print("\n3. Metadata field comparison:")
    try:
        metadata1 = {'priority': np.array(['high'])}
        metadata2 = {'priority': 'high'}
        
        # This comparison might cause issues:
        priority1 = metadata1.get('priority')
        priority2 = metadata2.get('priority')
        
        print(f"   Priority 1: {priority1} (type: {type(priority1)})")
        print(f"   Priority 2: {priority2} (type: {type(priority2)})")
        
        # Safe comparison:
        if isinstance(priority1, np.ndarray):
            priority1_safe = priority1.item() if priority1.size == 1 else priority1.tolist()
        else:
            priority1_safe = priority1
            
        print(f"   ✅ Safe comparison: {priority1_safe} == {priority2} -> {priority1_safe == priority2}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """
    Main debugging function.
    """
    print("🚀 SIMPLIFIED NUMPY BOOLEAN EVALUATION DEBUGGER")
    print("="*80)
    
    # Test specific patterns that might be causing issues
    test_specific_numpy_patterns()
    
    # Attempt the actual task update with detailed analysis
    result = safe_task_update_with_analysis()
    
    if result is None:
        print("\n💡 RECOMMENDATIONS BASED ON RESEARCH:")
        print("-" * 50)
        print("1. Replace 'if array:' with 'if array.any():' or 'if array.all():'")
        print("2. Replace 'array1 and array2' with 'array1 & array2' for element-wise operations")
        print("3. Replace 'array1 or array2' with 'array1 | array2' for element-wise operations")
        print("4. Use 'array.item()' for single-element arrays to get Python scalars")
        print("5. Use 'array.tolist()' to convert NumPy arrays to Python lists")
        print("6. Check for NumPy arrays in data before boolean operations")
        print("7. Use explicit comparisons: 'array.size > 0' instead of 'if array:'")
    
    print("\n✅ DEBUGGING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()