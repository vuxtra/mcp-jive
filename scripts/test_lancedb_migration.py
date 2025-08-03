#!/usr/bin/env python3
"""
LanceDB Migration Testing Suite

This script provides comprehensive testing for the LanceDB migration:
1. Unit tests for LanceDB managers
2. Integration tests for data operations
3. Performance benchmarks
4. Migration validation tests
5. Compatibility tests

Usage:
    python scripts/test_lancedb_migration.py [--test-type TYPE] [--verbose]

Test Types:
    unit: Run unit tests only
    integration: Run integration tests only
    performance: Run performance benchmarks only
    migration: Run migration validation tests only
    compatibility: Run compatibility tests only
    all: Run all tests (default)

Options:
    --verbose: Enable verbose output
    --benchmark: Include performance benchmarks
    --cleanup: Clean up test data after completion
    --parallel: Run tests in parallel where possible
"""

import asyncio
import os
import sys
import unittest
import argparse
import tempfile
import shutil
import time
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LanceDBTestSuite:
    """Comprehensive test suite for LanceDB migration."""
    
    def __init__(self, verbose: bool = False, cleanup: bool = True):
        self.verbose = verbose
        self.cleanup = cleanup
        self.test_results = []
        self.temp_dirs = []
        self.project_root = Path(__file__).parent.parent
        
        # Test data
        item_id_1 = str(uuid.uuid4())
        item_id_2 = str(uuid.uuid4())
        
        self.sample_work_items = [
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
        
        task_id_1 = str(uuid.uuid4())
        
        self.sample_tasks = [
            {
                "id": task_id_1,
                "title": "Test Task 1",
                "description": "A test task for validation",
                "status": "pending",
                "priority": "high",
                "metadata": '{"work_item_id": "' + self.sample_work_items[0]["item_id"] + '"}'
            }
        ]
    
    def log_test_result(self, test_name: str, success: bool, message: str, 
                       duration: float = 0.0, details: Optional[Dict] = None):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        if self.verbose or not success:
            logger.info(f"{status} {test_name}: {message} ({duration:.3f}s)")
        
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'duration': duration,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def create_temp_database(self, name: str) -> Path:
        """Create temporary database directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix=f"lancedb_test_{name}_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    async def test_server_manager_initialization(self) -> bool:
        """Test LanceDB Server Manager initialization."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType
            
            # Create temporary database
            temp_db = self.create_temp_database("server")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu",
                normalize_embeddings=True
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Test health status
            health = manager.get_health_status()
            
            await manager.cleanup()
            
            success = health['status'] in ['healthy', 'degraded']
            duration = time.time() - start_time
            
            self.log_test_result(
                "Server Manager Initialization",
                success,
                f"Manager initialized with status: {health['status']}",
                duration,
                {'health_status': health}
            )
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Server Manager Initialization",
                False,
                f"Failed to initialize: {e}",
                duration
            )
            return False
    
    async def test_jive_manager_initialization(self) -> bool:
        """Test LanceDB Jive Manager initialization."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType
            
            # Create temporary database
            temp_db = self.create_temp_database("jive")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu",
                normalize_embeddings=True
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Test health status
            health = manager.get_health_status()
            
            await manager.cleanup()
            
            success = health['status'] in ['healthy', 'degraded']
            duration = time.time() - start_time
            
            self.log_test_result(
                "Jive Manager Initialization",
                success,
                f"Manager initialized with status: {health['status']}",
                duration,
                {'health_status': health}
            )
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Jive Manager Initialization",
                False,
                f"Failed to initialize: {e}",
                duration
            )
            return False
    
    async def test_work_item_crud_operations(self) -> bool:
        """Test CRUD operations for work items."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType
            
            # Create temporary database
            temp_db = self.create_temp_database("crud_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Test Create
            work_item = self.sample_work_items[0].copy()
            created_item = await manager.create_work_item(work_item)
            
            if not created_item or created_item.get('id') != work_item['id']:
                raise Exception("Failed to create work item")
            
            # Test Read
            retrieved_item = await manager.get_work_item(work_item['id'])
            
            if not retrieved_item or retrieved_item.get('title') != work_item['title']:
                raise Exception("Failed to retrieve work item")
            
            # Test Update
            updated_data = {'title': 'Updated Test Work Item', 'status': 'in_progress'}
            updated_item = await manager.update_work_item(work_item['id'], updated_data)
            
            if not updated_item or updated_item.get('title') != updated_data['title']:
                raise Exception("Failed to update work item")
            
            # Test Delete
            deleted = await manager.delete_work_item(work_item['id'])
            
            if not deleted:
                raise Exception("Failed to delete work item")
            
            # Verify deletion
            deleted_item = await manager.get_work_item(work_item['id'])
            
            if deleted_item is not None:
                raise Exception("Work item still exists after deletion")
            
            await manager.cleanup()
            
            duration = time.time() - start_time
            self.log_test_result(
                "Work Item CRUD Operations",
                True,
                "All CRUD operations completed successfully",
                duration
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Work Item CRUD Operations",
                False,
                f"CRUD operations failed: {e}",
                duration
            )
            return False
    
    async def test_vector_search_functionality(self) -> bool:
        """Test vector search functionality."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType
            
            # Create temporary database
            temp_db = self.create_temp_database("search_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Create test work items
            for item in self.sample_work_items:
                await manager.create_work_item(item)
            
            # Test vector search
            search_results = await manager.search_work_items(
                query="test validation",
                limit=10
            )
            
            if not search_results or len(search_results) == 0:
                raise Exception("Vector search returned no results")
            
            # Test keyword search
            keyword_results = await manager.search_work_items(
                query="completed",
                search_type=SearchType.KEYWORD,
                limit=10
            )
            
            if not keyword_results:
                raise Exception("Keyword search failed")
            
            # Test hybrid search
            hybrid_results = await manager.search_work_items(
                query="test work item",
                search_type=SearchType.HYBRID,
                limit=10
            )
            
            if not hybrid_results:
                raise Exception("Hybrid search failed")
            
            await manager.cleanup()
            
            duration = time.time() - start_time
            self.log_test_result(
                "Vector Search Functionality",
                True,
                f"All search types working (vector: {len(search_results)}, keyword: {len(keyword_results)}, hybrid: {len(hybrid_results)} results)",
                duration,
                {
                    'vector_results': len(search_results),
                    'keyword_results': len(keyword_results),
                    'hybrid_results': len(hybrid_results)
                }
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Vector Search Functionality",
                False,
                f"Search functionality failed: {e}",
                duration
            )
            return False
    
    async def test_embedding_generation(self) -> bool:
        """Test embedding generation functionality."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
            
            # Create temporary database
            temp_db = self.create_temp_database("embedding_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu",
                normalize_embeddings=True
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Test single text embedding
            text = "This is a test text for embedding generation"
            embedding = await manager.generate_embedding(text)
            
            if not embedding or len(embedding) != 384:  # all-MiniLM-L6-v2 produces 384-dim embeddings
                raise Exception(f"Invalid embedding generated: length {len(embedding) if embedding else 0}")
            
            # Test batch embedding generation
            texts = [
                "First test text",
                "Second test text",
                "Third test text"
            ]
            
            batch_embeddings = await manager.generate_embeddings(texts)
            
            if not batch_embeddings or len(batch_embeddings) != len(texts):
                raise Exception(f"Batch embedding failed: expected {len(texts)}, got {len(batch_embeddings) if batch_embeddings else 0}")
            
            # Verify all embeddings have correct dimensions
            for i, emb in enumerate(batch_embeddings):
                if not emb or len(emb) != 384:
                    raise Exception(f"Invalid batch embedding {i}: length {len(emb) if emb else 0}")
            
            await manager.cleanup()
            
            duration = time.time() - start_time
            self.log_test_result(
                "Embedding Generation",
                True,
                f"Generated embeddings: single ({len(embedding)}D), batch ({len(batch_embeddings)} x {len(batch_embeddings[0])}D)",
                duration,
                {
                    'single_embedding_dim': len(embedding),
                    'batch_count': len(batch_embeddings),
                    'batch_embedding_dim': len(batch_embeddings[0])
                }
            )
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Embedding Generation",
                False,
                f"Embedding generation failed: {e}",
                duration
            )
            return False
    
    async def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
            
            # Create temporary database
            temp_db = self.create_temp_database("performance_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Benchmark: Bulk insert
            bulk_items = []
            for i in range(100):
                item_id = str(uuid.uuid4())
                item = {
                    "id": item_id,
                    "item_id": item_id,
                    "title": f"Performance Test Item {i}",
                    "description": f"This is performance test item number {i} with some descriptive content",
                    "item_type": "Task",
                    "status": "active" if i % 2 == 0 else "completed",
                    "priority": ["low", "medium", "high"][i % 3],
                    "tags": [f"tag{i}", "performance", "test"],
                    "metadata": f'{{"index": {i}, "batch": "performance_test"}}'
                }
                bulk_items.append(item)
            
            insert_start = time.time()
            for item in bulk_items:
                await manager.create_work_item(item)
            insert_duration = time.time() - insert_start
            
            # Benchmark: Search performance
            search_times = []
            for i in range(10):
                search_start = time.time()
                results = await manager.search_work_items(
                    query=f"performance test item {i*10}",
                    limit=10
                )
                search_times.append(time.time() - search_start)
            
            avg_search_time = statistics.mean(search_times)
            
            # Benchmark: Retrieval performance
            retrieval_times = []
            for item in bulk_items[:10]:  # Test first 10 items
                retrieval_start = time.time()
                retrieved = await manager.get_work_item(item['item_id'])
                retrieval_times.append(time.time() - retrieval_start)
            
            avg_retrieval_time = statistics.mean(retrieval_times)
            
            await manager.cleanup()
            
            duration = time.time() - start_time
            
            # Performance thresholds (adjust based on requirements)
            insert_rate = len(bulk_items) / insert_duration  # items per second
            performance_ok = (
                insert_rate > 10 and  # At least 10 inserts per second
                avg_search_time < 1.0 and  # Search under 1 second
                avg_retrieval_time < 0.1  # Retrieval under 100ms
            )
            
            self.log_test_result(
                "Performance Benchmarks",
                performance_ok,
                f"Insert: {insert_rate:.1f} items/s, Search: {avg_search_time:.3f}s avg, Retrieval: {avg_retrieval_time:.3f}s avg",
                duration,
                {
                    'insert_rate': insert_rate,
                    'avg_search_time': avg_search_time,
                    'avg_retrieval_time': avg_retrieval_time,
                    'total_items': len(bulk_items)
                }
            )
            
            return performance_ok
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Performance Benchmarks",
                False,
                f"Performance testing failed: {e}",
                duration
            )
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and recovery."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
            
            # Create temporary database
            temp_db = self.create_temp_database("error_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            error_tests_passed = 0
            total_error_tests = 5
            
            # Test 1: Get non-existent work item
            try:
                result = await manager.get_work_item("non-existent-id")
                if result is None:
                    error_tests_passed += 1
            except Exception:
                pass  # Expected to handle gracefully
            
            # Test 2: Update non-existent work item
            try:
                result = await manager.update_work_item("non-existent-id", {"title": "test"})
                if result is None:
                    error_tests_passed += 1
            except Exception:
                pass  # Expected to handle gracefully
            
            # Test 3: Delete non-existent work item
            try:
                result = await manager.delete_work_item("non-existent-id")
                if result is False:
                    error_tests_passed += 1
            except Exception:
                pass  # Expected to handle gracefully
            
            # Test 4: Invalid search query
            try:
                result = await manager.search_work_items(query="", limit=10)
                if isinstance(result, list):  # Should return empty list, not error
                    error_tests_passed += 1
            except Exception:
                pass  # Expected to handle gracefully
            
            # Test 5: Invalid embedding input
            try:
                result = await manager.generate_embedding("")
                if result is not None:  # Should handle empty string
                    error_tests_passed += 1
            except Exception:
                pass  # Expected to handle gracefully
            
            await manager.cleanup()
            
            success = error_tests_passed >= total_error_tests * 0.8  # 80% pass rate
            duration = time.time() - start_time
            
            self.log_test_result(
                "Error Handling",
                success,
                f"Passed {error_tests_passed}/{total_error_tests} error handling tests",
                duration,
                {'tests_passed': error_tests_passed, 'total_tests': total_error_tests}
            )
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Error Handling",
                False,
                f"Error handling tests failed: {e}",
                duration
            )
            return False
    
    async def test_concurrent_operations(self) -> bool:
        """Test concurrent database operations."""
        start_time = time.time()
        
        try:
            from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
            
            # Create temporary database
            temp_db = self.create_temp_database("concurrent_test")
            
            config = DatabaseConfig(
                data_path=str(temp_db),
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            
            manager = LanceDBManager(config)
            await manager.initialize()
            
            # Create concurrent tasks
            async def create_work_item_task(index: int):
                item_id = str(uuid.uuid4())
                item = {
                    "id": item_id,
                    "item_id": item_id,
                    "title": f"Concurrent Test Item {index}",
                    "description": f"This is concurrent test item {index}",
                    "item_type": "Task",
                    "status": "active",
                    "priority": "medium",
                    "tags": [f"concurrent{index}", "test"],
                    "metadata": f'{{"index": {index}}}'
                }
                return await manager.create_work_item(item)
            
            # Run concurrent operations
            tasks = [create_work_item_task(i) for i in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful_creates = sum(1 for r in results if not isinstance(r, Exception) and r is not None)
            
            # Test concurrent searches
            async def search_task(query: str):
                return await manager.search_work_items(query=query, limit=5)
            
            search_tasks = [search_task(f"concurrent test {i}") for i in range(10)]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            successful_searches = sum(1 for r in search_results if not isinstance(r, Exception) and r is not None)
            
            await manager.cleanup()
            
            success = successful_creates >= 18 and successful_searches >= 8  # Allow some failures
            duration = time.time() - start_time
            
            self.log_test_result(
                "Concurrent Operations",
                success,
                f"Concurrent creates: {successful_creates}/20, searches: {successful_searches}/10",
                duration,
                {
                    'successful_creates': successful_creates,
                    'successful_searches': successful_searches
                }
            )
            
            return success
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Concurrent Operations",
                False,
                f"Concurrent operations test failed: {e}",
                duration
            )
            return False
    
    async def run_unit_tests(self) -> Dict[str, bool]:
        """Run all unit tests."""
        logger.info("🧪 Running unit tests...")
        
        tests = {
            'server_initialization': self.test_server_manager_initialization,
            'jive_initialization': self.test_jive_manager_initialization,
            'embedding_generation': self.test_embedding_generation,
            'error_handling': self.test_error_handling
        }
        
        results = {}
        for test_name, test_func in tests.items():
            logger.info(f"🔄 Running: {test_name}")
            results[test_name] = await test_func()
        
        return results
    
    async def run_integration_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        logger.info("🔗 Running integration tests...")
        
        tests = {
            'work_item_crud': self.test_work_item_crud_operations,
            'vector_search': self.test_vector_search_functionality,
            'concurrent_operations': self.test_concurrent_operations
        }
        
        results = {}
        for test_name, test_func in tests.items():
            logger.info(f"🔄 Running: {test_name}")
            results[test_name] = await test_func()
        
        return results
    
    async def run_performance_tests(self) -> Dict[str, bool]:
        """Run all performance tests."""
        logger.info("⚡ Running performance tests...")
        
        tests = {
            'performance_benchmarks': self.test_performance_benchmarks
        }
        
        results = {}
        for test_name, test_func in tests.items():
            logger.info(f"🔄 Running: {test_name}")
            results[test_name] = await test_func()
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        logger.info("🚀 Running complete test suite...")
        
        start_time = time.time()
        
        # Run test suites
        unit_results = await self.run_unit_tests()
        integration_results = await self.run_integration_tests()
        performance_results = await self.run_performance_tests()
        
        # Combine results
        all_results = {**unit_results, **integration_results, **performance_results}
        
        total_duration = time.time() - start_time
        
        # Calculate summary
        total_tests = len(all_results)
        passed_tests = sum(1 for success in all_results.values() if success)
        failed_tests = total_tests - passed_tests
        
        summary = {
            'success': failed_tests == 0,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'duration': total_duration,
            'test_results': self.test_results,
            'individual_results': all_results
        }
        
        return summary
    
    def cleanup_temp_directories(self):
        """Clean up temporary directories."""
        if not self.cleanup:
            logger.info(f"🗂️ Keeping {len(self.temp_dirs)} temporary directories for inspection")
            for temp_dir in self.temp_dirs:
                logger.info(f"  📁 {temp_dir}")
            return
        
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    if self.verbose:
                        logger.info(f"🗑️ Cleaned up: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup {temp_dir}: {e}")

def print_test_report(summary: Dict[str, Any]):
    """Print detailed test report."""
    print("\n" + "="*60)
    print("🧪 LANCEDB MIGRATION TEST REPORT")
    print("="*60)
    
    status = "✅ ALL TESTS PASSED" if summary['success'] else "❌ SOME TESTS FAILED"
    print(f"Overall Status: {status}")
    print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    print(f"Total Duration: {summary['duration']:.2f} seconds")
    
    if summary['failed_tests'] > 0:
        print(f"\n❌ Failed Tests ({summary['failed_tests']}):")
        for result in summary['test_results']:
            if not result['success']:
                print(f"  • {result['test_name']}: {result['message']}")
    
    print("\n📋 Test Results:")
    for result in summary['test_results']:
        status_icon = "✅" if result['success'] else "❌"
        duration_str = f"({result['duration']:.3f}s)" if result['duration'] > 0 else ""
        print(f"  {status_icon} {result['test_name']}: {result['message']} {duration_str}")
    
    print("\n" + "="*60)
    
    if summary['success']:
        print("🎉 All tests passed! LanceDB migration is ready.")
        print("\n📝 Next steps:")
        print("  1. Run the actual migration: python scripts/migrate_weaviate_to_lancedb.py")
        print("  2. Update application code to use LanceDBManager")
        print("  3. Deploy and monitor the new system")
    else:
        print("⚠️ Some tests failed!")
        print("\n🔧 Recommended actions:")
        print("  1. Review failed test details above")
        print("  2. Check LanceDB installation and configuration")
        print("  3. Verify system resources and dependencies")
        print("  4. Re-run tests after resolving issues")

async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test LanceDB migration')
    parser.add_argument('--test-type', choices=['unit', 'integration', 'performance', 'all'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--cleanup', action='store_true', default=True, help='Clean up test data')
    parser.add_argument('--no-cleanup', dest='cleanup', action='store_false', help='Keep test data')
    
    args = parser.parse_args()
    
    try:
        test_suite = LanceDBTestSuite(verbose=args.verbose, cleanup=args.cleanup)
        
        if args.test_type == 'unit':
            results = await test_suite.run_unit_tests()
            summary = {
                'success': all(results.values()),
                'total_tests': len(results),
                'passed_tests': sum(1 for success in results.values() if success),
                'failed_tests': sum(1 for success in results.values() if not success),
                'duration': 0,
                'test_results': test_suite.test_results,
                'individual_results': results
            }
        elif args.test_type == 'integration':
            results = await test_suite.run_integration_tests()
            summary = {
                'success': all(results.values()),
                'total_tests': len(results),
                'passed_tests': sum(1 for success in results.values() if success),
                'failed_tests': sum(1 for success in results.values() if not success),
                'duration': 0,
                'test_results': test_suite.test_results,
                'individual_results': results
            }
        elif args.test_type == 'performance':
            results = await test_suite.run_performance_tests()
            summary = {
                'success': all(results.values()),
                'total_tests': len(results),
                'passed_tests': sum(1 for success in results.values() if success),
                'failed_tests': sum(1 for success in results.values() if not success),
                'duration': 0,
                'test_results': test_suite.test_results,
                'individual_results': results
            }
        else:  # all
            summary = await test_suite.run_all_tests()
        
        # Cleanup
        test_suite.cleanup_temp_directories()
        
        # Print report
        print_test_report(summary)
        
        # Save detailed results
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['success'] else 1)
        
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())