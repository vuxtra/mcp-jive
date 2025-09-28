#!/usr/bin/env python3
"""
Detailed FTS debugging to understand indexing and querying issues
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

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_fts_detailed():
    """Detailed FTS debugging."""
    temp_dir = tempfile.mkdtemp(prefix="fts_detailed_")
    logger.info(f"🔧 Created test environment: {temp_dir}")
    
    try:
        config = DatabaseConfig(
            data_path=temp_dir,
            embedding_model="all-MiniLM-L6-v2",
            device="cpu",
            enable_fts=True
        )
        
        manager = LanceDBManager(config)
        await manager.initialize()
        
        # Create test data
        test_item = {
            "id": "test-fts-1",
            "title": "Test Item",
            "description": "This is a test description",
            "item_type": "Task",
            "status": "completed",
            "priority": "high",
            "acceptance_criteria": "Should work properly"
        }
        
        logger.info("📝 Creating test item...")
        result = await manager.create_work_item(test_item)
        logger.info(f"✅ Created: {result['id']} - status: {result['status']}")
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Get table and inspect
        table = manager.get_table("WorkItem")
        logger.info(f"📊 Table row count: {table.count_rows()}")
        
        # Check table schema
        schema = table.schema
        logger.info(f"📋 Table schema fields: {[field.name for field in schema]}")
        
        # List all indexes
        try:
            indexes = table.list_indices()
            logger.info(f"📋 Available indexes: {indexes}")
        except Exception as e:
            logger.warning(f"⚠️ Could not list indexes: {e}")
        
        # Check if FTS index exists
        try:
            # Try to get FTS index info
            import lancedb
            logger.info(f"🔍 LanceDB version: {lancedb.__version__}")
        except Exception as e:
            logger.warning(f"⚠️ Could not get LanceDB version: {e}")
        
        # Test various FTS queries
        test_queries = [
            "completed",
            "test",
            "high",
            "Task",
            "description"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing FTS query: '{query}'")
            
            # Direct FTS search
            try:
                fts_results = table.search(query, query_type="fts").limit(10).to_pandas()
                logger.info(f"📊 Direct FTS returned {len(fts_results)} results")
                if len(fts_results) > 0:
                    for idx, row in fts_results.iterrows():
                        logger.info(f"  - {row['title']} (status: {row['status']})")
            except Exception as e:
                logger.error(f"❌ Direct FTS failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Manager keyword search
            try:
                keyword_results = await manager.search_work_items(
                    query=query,
                    search_type=SearchType.KEYWORD,
                    limit=10
                )
                logger.info(f"📊 Manager keyword search returned {len(keyword_results)} results")
                for result in keyword_results:
                    logger.info(f"  - {result['title']} (status: {result['status']})")
            except Exception as e:
                logger.error(f"❌ Manager keyword search failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Test manual FTS index creation
        logger.info("\n🔧 Testing manual FTS index creation...")
        try:
            # Try to recreate FTS index with verbose logging
            text_fields = ['title', 'description', 'acceptance_criteria', 'status', 'priority', 'item_type']
            logger.info(f"🔍 Creating FTS index for fields: {text_fields}")
            
            table.create_fts_index(
                text_fields,
                replace=True,
                use_tantivy=True,
                with_position=True,
                base_tokenizer="simple",
                language="English",
                lower_case=True,
                stem=True,
                remove_stop_words=True,
                ascii_folding=True
            )
            logger.info("✅ Manual FTS index creation successful")
            
            # Wait and test again
            await asyncio.sleep(1)
            
            # Test after manual index creation
            logger.info("\n🔍 Testing after manual index creation...")
            fts_results = table.search("completed", query_type="fts").limit(10).to_pandas()
            logger.info(f"📊 Post-manual FTS returned {len(fts_results)} results")
            
        except Exception as e:
            logger.error(f"❌ Manual FTS index creation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with different tokenizers
        logger.info("\n🔧 Testing different tokenizer configurations...")
        tokenizer_configs = [
            {"base_tokenizer": "whitespace", "use_tantivy": True},
            {"base_tokenizer": "raw", "use_tantivy": True},
            {"base_tokenizer": "simple", "use_tantivy": False},
        ]
        
        for i, config in enumerate(tokenizer_configs):
            try:
                logger.info(f"🔍 Testing tokenizer config {i+1}: {config}")
                table.create_fts_index(
                    ['status', 'priority'],  # Simple fields
                    replace=True,
                    **config
                )
                
                await asyncio.sleep(0.5)
                
                fts_results = table.search("completed", query_type="fts").limit(10).to_pandas()
                logger.info(f"📊 Config {i+1} returned {len(fts_results)} results")
                
            except Exception as e:
                logger.error(f"❌ Tokenizer config {i+1} failed: {e}")
        
        # Test raw table data
        logger.info("\n📋 Raw table data:")
        all_data = table.search().limit(10).to_pandas()
        for idx, row in all_data.iterrows():
            logger.info(f"  Row {idx}: title='{row['title']}', status='{row['status']}', priority='{row['priority']}'")
        
        await manager.cleanup()
        
    except Exception as e:
        logger.error(f"❌ Detailed FTS debug failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)
            logger.info(f"🧹 Cleaned up: {temp_dir}")

if __name__ == "__main__":
    asyncio.run(debug_fts_detailed())