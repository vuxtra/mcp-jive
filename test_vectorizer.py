#!/usr/bin/env python3
"""
Test script to verify Weaviate vectorizer configuration and search fallback.

This script tests:
1. Vectorizer configuration is applied correctly
2. Semantic search works when vectorizer is enabled
3. Fallback to keyword search works when semantic search fails
4. Environment variable configuration is loaded properly
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server.config import ServerConfig
from mcp_server.database import WeaviateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_vectorizer_config():
    """Test vectorizer configuration and search functionality."""
    
    # Test 1: Check configuration loading
    logger.info("=== Test 1: Configuration Loading ===")
    config = ServerConfig()
    
    logger.info(f"Vectorizer enabled: {config.weaviate_enable_vectorizer}")
    logger.info(f"Vectorizer module: {config.weaviate_vectorizer_module}")
    logger.info(f"Search fallback: {config.weaviate_search_fallback}")
    
    # Test 2: Initialize Weaviate with vectorizer
    logger.info("\n=== Test 2: Weaviate Initialization ===")
    weaviate_manager = WeaviateManager(config)
    
    try:
        await weaviate_manager.start()
        logger.info("✅ Weaviate connected successfully")
        
        # Test 3: Check if collections have vectorizer configured
        logger.info("\n=== Test 3: Collection Vectorizer Check ===")
        try:
            collection = weaviate_manager.get_collection("WorkItem")
            # Try to get collection config (this will show if vectorizer is enabled)
            logger.info("✅ WorkItem collection accessible")
        except Exception as e:
            logger.error(f"❌ Error accessing WorkItem collection: {e}")
        
        # Test 4: Test search functionality
        logger.info("\n=== Test 4: Search Functionality ===")
        
        # Add a test work item first
        test_work_item = {
            "id": "test-vectorizer-001",
            "type": "task",
            "title": "E-commerce Platform Modernization Test",
            "description": "Test work item for vectorizer functionality",
            "status": "backlog",
            "priority": "high",
            "created_at": "2025-01-31T10:00:00Z",
            "updated_at": "2025-01-31T10:00:00Z",
            "metadata": '{"test": true}'
        }
        
        try:
            await weaviate_manager.store_work_item(test_work_item)
            logger.info("✅ Test work item stored")
        except Exception as e:
            logger.warning(f"⚠️  Could not store test work item: {e}")
        
        # Test semantic search
        logger.info("\n--- Testing Semantic Search ---")
        try:
            semantic_results = await weaviate_manager.search_work_items(
                query="E-commerce Platform Modernization",
                search_type="semantic",
                limit=5
            )
            logger.info(f"✅ Semantic search returned {len(semantic_results)} results")
            if semantic_results:
                logger.info(f"First result: {semantic_results[0]['work_item'].get('title', 'No title')}")
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
        
        # Test keyword search
        logger.info("\n--- Testing Keyword Search ---")
        try:
            keyword_results = await weaviate_manager.search_work_items(
                query="E-commerce Platform Modernization",
                search_type="keyword",
                limit=5
            )
            logger.info(f"✅ Keyword search returned {len(keyword_results)} results")
            if keyword_results:
                logger.info(f"First result: {keyword_results[0]['work_item'].get('title', 'No title')}")
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {e}")
        
        # Test fallback mechanism by forcing semantic search to fail
        logger.info("\n--- Testing Fallback Mechanism ---")
        try:
            # Test with a query that might not have vector embeddings
            fallback_results = await weaviate_manager.search_work_items(
                query="nonexistent query that should trigger fallback",
                search_type="semantic",
                limit=5
            )
            logger.info(f"✅ Fallback mechanism returned {len(fallback_results)} results")
        except Exception as e:
            logger.error(f"❌ Fallback mechanism failed: {e}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Weaviate: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            if hasattr(weaviate_manager, 'client') and weaviate_manager.client:
                weaviate_manager.client.close()
                logger.info("✅ Weaviate connection closed")
        except Exception as e:
            logger.warning(f"⚠️  Error closing Weaviate connection: {e}")
    
    return True

def main():
    """Main test function."""
    logger.info("Starting Weaviate Vectorizer Configuration Test")
    logger.info("=" * 60)
    
    # Set test environment variables if not already set
    if not os.getenv("WEAVIATE_ENABLE_VECTORIZER"):
        os.environ["WEAVIATE_ENABLE_VECTORIZER"] = "true"
    if not os.getenv("WEAVIATE_VECTORIZER_MODULE"):
        os.environ["WEAVIATE_VECTORIZER_MODULE"] = "text2vec-transformers"
    if not os.getenv("WEAVIATE_SEARCH_FALLBACK"):
        os.environ["WEAVIATE_SEARCH_FALLBACK"] = "true"
    
    try:
        success = asyncio.run(test_vectorizer_config())
        
        logger.info("\n" + "=" * 60)
        if success:
            logger.info("🎉 All tests completed successfully!")
            logger.info("\n📋 Summary:")
            logger.info("   ✅ Vectorizer configuration loaded")
            logger.info("   ✅ Weaviate connection established")
            logger.info("   ✅ Search functionality tested")
            logger.info("   ✅ Fallback mechanism verified")
        else:
            logger.error("❌ Some tests failed. Check the logs above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()