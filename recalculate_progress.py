#!/usr/bin/env python3
"""
Script to recalculate progress for all work items.
This will fix any existing work items that have incorrect progress values.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_jive.services.progress_calculator import ProgressCalculator
from mcp_jive.storage.work_item_storage import WorkItemStorage

async def main():
    """Recalculate progress for all work items."""
    try:
        print("Initializing storage and progress calculator...")
        storage = WorkItemStorage()
        calc = ProgressCalculator(storage)
        
        print("Starting progress recalculation for all work items...")
        result = await calc.recalculate_hierarchy_progress()
        
        if result.get('success'):
            print(f"✅ Success! Recalculated progress for {result.get('count', 0)} items")
            print(f"Updated items: {result.get('updated_items', [])}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during recalculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())