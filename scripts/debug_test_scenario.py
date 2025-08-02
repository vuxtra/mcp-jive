#!/usr/bin/env python3
"""
Debug the specific test scenario that's failing
"""

import asyncio
import logging
import sys
import tempfile
import shutil
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_test_scenario():
    """Debug the exact test scenario that's failing."""
    temp_dir = tempfile.mkdtemp(prefix="debug_test_")
    logger.info(f"🔧 Created test environment: {temp_dir}")
    
    try:
        # Create the exact same configuration as the test
        config = DatabaseConfig(
            data_path=temp_dir,
            embedding_model="all-MiniLM-L6-v2",
            device="cpu",
            enable_fts=True
        )
        
        manager = LanceDBManager(config)
        await manager.initialize()
        
        # Create the exact same test data as the failing test
        item_id_1 = str(uuid.uuid4())
        item_id_2 = str(uuid.uuid4())
        
        sample_work_items = [
            {
                "id": item_id_1,
                "item_id": item_id_1,
                "title": "Test Work Item 1",
                "description": "This is a test work item for validation",
                "item_type": "Task",
                "status": "active",
                "priority": "high",
                "tags": ["test", "validation"],
                "metadata": '{"created_by": "test_suite", "version": "1.0"}'
            },
            {
                "id": item_id_2,
                "item_id": item_id_2,
                "title": "Test Work Item 2",
                "description": "Another test work item with different content",
                "item_type": "Story",
                "status": "completed",
                "priority": "medium",
                "tags": ["test", "completed"],
                "metadata": '{"created_by": "test_suite", "version": "1.1"}'
            }
        ]
        
        # Create test work items
        logger.info("📝 Creating test work items...")
        for item in sample_work_items:
            result = await manager.create_work_item(item)
            logger.info(f"✅ Created work item: {result['id']} - {result['title']} (status: {result['status']})")
        
        # Wait a moment for indexing
        await asyncio.sleep(1)
        
        # Check table contents
        table = manager.get_table("WorkItem")
        count = table.count_rows()
        logger.info(f"📊 Table has {count} rows")
        
        # List all data to see what we have
        all_data = table.search().limit(10).to_pandas()
        logger.info(f"📋 All data in table:")
        for idx, row in all_data.iterrows():
            logger.info(f"  - {row['title']} (status: {row['status']}, priority: {row['priority']})")
        
        # Test the exact same searches as the failing test
        logger.info("\n🔍 Testing vector search for 'test validation'...")
        try:
            search_results = await manager.search_work_items(
                query="test validation",
                limit=10
            )
            logger.info(f"📊 Vector search returned {len(search_results)} results")
            for result in search_results:
                logger.info(f"  - {result['title']} (score: {result.get('_distance', 'N/A')})")
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
        
        logger.info("\n🔍 Testing keyword search for 'completed'...")
        try:
            keyword_results = await manager.search_work_items(
                query="completed",
                search_type=SearchType.KEYWORD,
                limit=10
            )
            logger.info(f"📊 Keyword search returned {len(keyword_results)} results")
            for result in keyword_results:
                logger.info(f"  - {result['title']} (status: {result['status']})")
                
            if len(keyword_results) == 0:
                logger.warning("⚠️ Keyword search returned no results - testing fallback...")
                
                # Test with FTS disabled to see if fallback works
                original_fts = manager.config.enable_fts
                manager.config.enable_fts = False
                
                fallback_results = await manager.search_work_items(
                    query="completed",
                    search_type=SearchType.KEYWORD,
                    limit=10
                )
                logger.info(f"📊 Fallback search returned {len(fallback_results)} results")
                for result in fallback_results:
                    logger.info(f"  - {result['title']} (status: {result['status']})")
                
                # Restore FTS setting
                manager.config.enable_fts = original_fts
                
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info("\n🔍 Testing hybrid search for 'test work item'...")
        try:
            hybrid_results = await manager.search_work_items(
                query="test work item",
                search_type=SearchType.HYBRID,
                limit=10
            )
            logger.info(f"📊 Hybrid search returned {len(hybrid_results)} results")
            for result in hybrid_results:
                logger.info(f"  - {result['title']}")
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test direct FTS search
        logger.info("\n🔍 Testing direct FTS search...")
        try:
            direct_results = table.search("completed", query_type="fts").limit(10).to_pandas()
            logger.info(f"📊 Direct FTS search returned {len(direct_results)} results")
            for idx, row in direct_results.iterrows():
                logger.info(f"  - {row['title']} (status: {row['status']})")
        except Exception as e:
            logger.error(f"❌ Direct FTS search failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test LIKE search
        logger.info("\n🔍 Testing LIKE search...")
        try:
            like_results = table.search().where(
                "title LIKE '%completed%' OR description LIKE '%completed%' OR status LIKE '%completed%' OR priority LIKE '%completed%'"
            ).limit(10).to_pandas()
            logger.info(f"📊 LIKE search returned {len(like_results)} results")
            for idx, row in like_results.iterrows():
                logger.info(f"  - {row['title']} (status: {row['status']})")
        except Exception as e:
            logger.error(f"❌ LIKE search failed: {e}")
            import traceback
            traceback.print_exc()
        
        await manager.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Cleaned up test environment: {temp_dir}")

if __name__ == "__main__":
    asyncio.run(debug_test_scenario())