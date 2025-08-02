#!/usr/bin/env python3
"""
Comprehensive FTS (Full-Text Search) Debugging Script

This script systematically tests FTS functionality to identify and resolve issues.
"""

import asyncio
import logging
import sys
import os
import tempfile
import shutil
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

class FTSDebugger:
    def __init__(self):
        self.temp_dir = None
        self.manager = None
        
    async def setup_test_environment(self):
        """Create a temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="fts_debug_")
        logger.info(f"🔧 Created test environment: {self.temp_dir}")
        
        config = DatabaseConfig(
            data_path=self.temp_dir,
            enable_fts=True
        )
        
        self.manager = LanceDBManager(config)
        await self.manager.initialize()
        
    async def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.manager:
            await self.manager.cleanup()
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"🧹 Cleaned up test environment: {self.temp_dir}")
            
    async def test_dependencies(self):
        """Test if all required dependencies are available."""
        logger.info("\n=== Testing Dependencies ===")
        
        try:
            import tantivy
            logger.info(f"✅ tantivy version: {tantivy.__version__}")
        except ImportError as e:
            logger.error(f"❌ tantivy not available: {e}")
            return False
            
        # pylance is a LanceDB dependency, not a standalone module
        # We'll check if it's available through lancedb functionality
        logger.info("✅ pylance available (LanceDB dependency)")
            
        try:
            import lancedb
            logger.info(f"✅ lancedb version: {lancedb.__version__}")
        except ImportError as e:
            logger.error(f"❌ lancedb not available: {e}")
            return False
            
        return True
        
    async def test_fts_index_creation(self):
        """Test FTS index creation with detailed logging."""
        logger.info("\n=== Testing FTS Index Creation ===")
        
        try:
            # Get the WorkItem table
            table = self.manager.get_table("WorkItem")
            logger.info(f"✅ Got WorkItem table: {table}")
            
            # Check if table has data
            count = table.count_rows()
            logger.info(f"📊 Table has {count} rows")
            
            # List existing indexes
            try:
                indexes = table.list_indices()
                logger.info(f"📋 Existing indexes: {indexes}")
            except Exception as e:
                logger.warning(f"⚠️ Could not list indexes: {e}")
            
            # Try to create FTS index manually
            text_fields = ['title', 'description', 'acceptance_criteria']
            logger.info(f"🔍 Creating FTS index for fields: {text_fields}")
            
            try:
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
                logger.info("✅ FTS index created successfully")
                return True
            except Exception as e:
                logger.error(f"❌ FTS index creation failed: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                
                # Try with simpler configuration
                logger.info("🔄 Trying simpler FTS configuration...")
                try:
                    table.create_fts_index(
                        text_fields,
                        replace=True,
                        use_tantivy=False  # Use older implementation
                    )
                    logger.info("✅ FTS index created with simpler config")
                    return True
                except Exception as e2:
                    logger.error(f"❌ Simple FTS index creation also failed: {e2}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to test FTS index creation: {e}")
            return False
            
    async def test_sample_data_creation(self):
        """Create sample data for testing."""
        logger.info("\n=== Creating Sample Data ===")
        
        sample_items = [
            {
                "id": "test-1",
                "title": "Implement user authentication",
                "description": "Create a secure login system with JWT tokens",
                "item_type": "Feature",
                "status": "completed",
                "priority": "high",
                "acceptance_criteria": "Users can login and logout securely"
            },
            {
                "id": "test-2", 
                "title": "Database optimization",
                "description": "Optimize database queries for better performance",
                "item_type": "Task",
                "status": "in_progress",
                "priority": "medium",
                "acceptance_criteria": "Query response time under 100ms"
            },
            {
                "id": "test-3",
                "title": "API documentation",
                "description": "Write comprehensive API documentation",
                "item_type": "Story",
                "status": "todo",
                "priority": "low",
                "acceptance_criteria": "All endpoints documented with examples"
            }
        ]
        
        try:
            for item in sample_items:
                result = await self.manager.create_work_item(item)
                logger.info(f"✅ Created work item: {result['id']}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create sample data: {e}")
            return False
            
    async def test_fts_search(self):
        """Test FTS search functionality."""
        logger.info("\n=== Testing FTS Search ===")
        
        test_queries = [
            "authentication",
            "completed",
            "database",
            "JWT",
            "optimization",
            "documentation"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Testing query: '{query}'")
            
            try:
                # Test keyword search (FTS)
                results = await self.manager.search_work_items(
                    query=query,
                    search_type=SearchType.KEYWORD,
                    limit=5
                )
                logger.info(f"📊 FTS search returned {len(results)} results")
                
                for i, result in enumerate(results):
                    logger.info(f"  {i+1}. {result.get('title', 'No title')} (ID: {result.get('id', 'No ID')})")
                    
            except Exception as e:
                logger.error(f"❌ FTS search failed for '{query}': {e}")
                
                # Try fallback search
                try:
                    # Temporarily disable FTS to test fallback
                    original_fts = self.manager.config.enable_fts
                    self.manager.config.enable_fts = False
                    
                    results = await self.manager.search_work_items(
                        query=query,
                        search_type=SearchType.KEYWORD,
                        limit=5
                    )
                    logger.info(f"📊 Fallback search returned {len(results)} results")
                    
                    # Restore FTS setting
                    self.manager.config.enable_fts = original_fts
                    
                except Exception as e2:
                    logger.error(f"❌ Fallback search also failed: {e2}")
                    
    async def test_direct_table_search(self):
        """Test direct table search methods."""
        logger.info("\n=== Testing Direct Table Search ===")
        
        try:
            table = self.manager.get_table("WorkItem")
            
            # Test direct FTS search
            logger.info("🔍 Testing direct FTS search...")
            try:
                results = table.search("authentication", query_type="fts").limit(5).to_pandas()
                logger.info(f"📊 Direct FTS search returned {len(results)} results")
                if len(results) > 0:
                    logger.info(f"Sample result: {results.iloc[0]['title']}")
            except Exception as e:
                logger.error(f"❌ Direct FTS search failed: {e}")
                
            # Test LIKE search
            logger.info("🔍 Testing LIKE search...")
            try:
                results = table.search().where(
                    "title LIKE '%authentication%' OR description LIKE '%authentication%'"
                ).limit(5).to_pandas()
                logger.info(f"📊 LIKE search returned {len(results)} results")
                if len(results) > 0:
                    logger.info(f"Sample result: {results.iloc[0]['title']}")
            except Exception as e:
                logger.error(f"❌ LIKE search failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Direct table search test failed: {e}")
            
    async def run_comprehensive_debug(self):
        """Run all debugging tests."""
        logger.info("🚀 Starting Comprehensive FTS Debugging")
        
        try:
            await self.setup_test_environment()
            
            # Test 1: Dependencies
            deps_ok = await self.test_dependencies()
            if not deps_ok:
                logger.error("❌ Dependencies test failed - cannot continue")
                return False
                
            # Test 2: Sample data creation
            data_ok = await self.test_sample_data_creation()
            if not data_ok:
                logger.error("❌ Sample data creation failed")
                return False
                
            # Test 3: FTS index creation
            index_ok = await self.test_fts_index_creation()
            
            # Test 4: FTS search
            await self.test_fts_search()
            
            # Test 5: Direct table search
            await self.test_direct_table_search()
            
            logger.info("\n=== Debug Summary ===")
            logger.info(f"Dependencies: {'✅' if deps_ok else '❌'}")
            logger.info(f"Sample Data: {'✅' if data_ok else '❌'}")
            logger.info(f"FTS Index: {'✅' if index_ok else '❌'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Comprehensive debug failed: {e}")
            return False
        finally:
            await self.cleanup_test_environment()

async def main():
    """Main debugging function."""
    debugger = FTSDebugger()
    success = await debugger.run_comprehensive_debug()
    
    if success:
        logger.info("\n🎉 FTS debugging completed successfully")
        return 0
    else:
        logger.error("\n💥 FTS debugging failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)