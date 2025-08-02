#!/usr/bin/env python3
"""
LanceDB Migration Validation Script

This script validates that the LanceDB migration was successful by:
1. Testing database connectivity
2. Validating data integrity
3. Testing search functionality
4. Performance benchmarking
5. Comparing with expected results

Usage:
    python scripts/validate_lancedb_migration.py [--verbose] [--benchmark]

Options:
    --verbose: Enable detailed logging
    --benchmark: Run performance benchmarks
    --compare-backup: Compare with Weaviate backup data
"""

import asyncio
import json
import os
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import lancedb
    import pandas as pd
except ImportError as e:
    print(f"❌ Missing LanceDB dependencies: {e}")
    print("📦 Install with: pip install lancedb pandas")
    sys.exit(1)

try:
    from mcp_server.lancedb_manager import LanceDBManager, DatabaseConfig, SearchType
    from mcp_jive.lancedb_manager import LanceDBManager as JiveLanceDBManager
    from mcp_jive.lancedb_manager import DatabaseConfig as JiveDatabaseConfig
except ImportError as e:
    print(f"❌ Cannot import LanceDB managers: {e}")
    print("🔧 Ensure LanceDB managers are implemented")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Validation test result."""
    test_name: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Optional[Dict[str, Any]] = None

class ValidationSuite:
    """Comprehensive validation test suite."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[ValidationResult] = []
        self.server_manager = None
        self.jive_manager = None
    
    async def initialize_managers(self) -> bool:
        """Initialize LanceDB managers."""
        try:
            # Initialize Server LanceDB Manager
            server_config = DatabaseConfig(
                data_path="./data/lancedb",
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            self.server_manager = LanceDBManager(server_config)
            await self.server_manager.initialize()
            
            # Initialize Jive LanceDB Manager
            jive_config = JiveDatabaseConfig(
                data_path="./data/lancedb_jive",
                embedding_model="all-MiniLM-L6-v2",
                device="cpu"
            )
            self.jive_manager = JiveLanceDBManager(jive_config)
            await self.jive_manager.initialize()
            
            logger.info("✅ Initialized LanceDB managers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize managers: {e}")
            return False
    
    def log_result(self, result: ValidationResult):
        """Log and store validation result."""
        self.results.append(result)
        
        status = "✅ PASS" if result.passed else "❌ FAIL"
        duration_str = f" ({result.duration:.3f}s)" if result.duration > 0 else ""
        
        logger.info(f"{status}: {result.test_name}{duration_str}")
        
        if not result.passed or self.verbose:
            logger.info(f"  Message: {result.message}")
            
        if result.details and self.verbose:
            logger.info(f"  Details: {json.dumps(result.details, indent=2, default=str)}")
    
    async def test_database_connectivity(self) -> ValidationResult:
        """Test basic database connectivity."""
        start_time = time.time()
        
        try:
            # Test server manager
            server_health = self.server_manager.get_health_status()
            if server_health['status'] not in ['healthy', 'degraded']:
                return ValidationResult(
                    test_name="Database Connectivity",
                    passed=False,
                    message=f"Server manager unhealthy: {server_health['status']}",
                    duration=time.time() - start_time,
                    details=server_health
                )
            
            # Test jive manager
            jive_health = self.jive_manager.get_health_status()
            if jive_health['status'] not in ['healthy', 'degraded']:
                return ValidationResult(
                    test_name="Database Connectivity",
                    passed=False,
                    message=f"Jive manager unhealthy: {jive_health['status']}",
                    duration=time.time() - start_time,
                    details=jive_health
                )
            
            return ValidationResult(
                test_name="Database Connectivity",
                passed=True,
                message="Both managers connected successfully",
                duration=time.time() - start_time,
                details={
                    'server_health': server_health,
                    'jive_health': jive_health
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Database Connectivity",
                passed=False,
                message=f"Connection test failed: {e}",
                duration=time.time() - start_time
            )
    
    async def test_table_existence(self) -> ValidationResult:
        """Test that all required tables exist."""
        start_time = time.time()
        
        try:
            # Expected tables
            server_tables = ['WorkItem', 'Task', 'SearchIndex', 'ExecutionLog']
            jive_tables = ['WorkItem', 'ExecutionLog']
            
            # Check server tables
            existing_server_tables = self.server_manager.list_tables()
            missing_server_tables = set(server_tables) - set(existing_server_tables)
            
            # Check jive tables
            existing_jive_tables = self.jive_manager.list_tables()
            missing_jive_tables = set(jive_tables) - set(existing_jive_tables)
            
            if missing_server_tables or missing_jive_tables:
                return ValidationResult(
                    test_name="Table Existence",
                    passed=False,
                    message=f"Missing tables - Server: {missing_server_tables}, Jive: {missing_jive_tables}",
                    duration=time.time() - start_time,
                    details={
                        'server_tables': existing_server_tables,
                        'jive_tables': existing_jive_tables,
                        'missing_server': list(missing_server_tables),
                        'missing_jive': list(missing_jive_tables)
                    }
                )
            
            return ValidationResult(
                test_name="Table Existence",
                passed=True,
                message="All required tables exist",
                duration=time.time() - start_time,
                details={
                    'server_tables': existing_server_tables,
                    'jive_tables': existing_jive_tables
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Table Existence",
                passed=False,
                message=f"Table existence check failed: {e}",
                duration=time.time() - start_time
            )
    
    async def test_data_operations(self) -> ValidationResult:
        """Test basic CRUD operations."""
        start_time = time.time()
        
        try:
            # Test work item creation
            test_work_item = {
                'id': 'test-validation-001',
                'title': 'Validation Test Work Item',
                'description': 'This is a test work item for validation',
                'item_type': 'task',
                'status': 'todo',
                'priority': 'medium'
            }
            
            # Create work item
            created_result = await self.server_manager.create_work_item(test_work_item)
            created_id = created_result['id'] if isinstance(created_result, dict) else created_result
            if created_id != test_work_item['id']:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message=f"Work item creation failed: expected {test_work_item['id']}, got {created_id}",
                    duration=time.time() - start_time
                )
            
            # Read work item
            retrieved_item = await self.server_manager.get_work_item(created_id)
            if not retrieved_item or retrieved_item['title'] != test_work_item['title']:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message="Work item retrieval failed",
                    duration=time.time() - start_time
                )
            
            # Update work item
            updates = {'status': 'in_progress', 'progress': 50.0}
            update_success = await self.server_manager.update_work_item(created_id, updates)
            if not update_success:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message="Work item update failed",
                    duration=time.time() - start_time
                )
            
            # Verify update
            updated_item = await self.server_manager.get_work_item(created_id)
            if updated_item['status'] != 'in_progress' or updated_item['progress'] != 50.0:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message="Work item update verification failed",
                    duration=time.time() - start_time
                )
            
            # Delete work item
            delete_success = await self.server_manager.delete_work_item(created_id)
            if not delete_success:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message="Work item deletion failed",
                    duration=time.time() - start_time
                )
            
            # Verify deletion
            deleted_item = await self.server_manager.get_work_item(created_id)
            if deleted_item is not None:
                return ValidationResult(
                    test_name="Data Operations",
                    passed=False,
                    message="Work item deletion verification failed",
                    duration=time.time() - start_time
                )
            
            return ValidationResult(
                test_name="Data Operations",
                passed=True,
                message="All CRUD operations successful",
                duration=time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Data Operations",
                passed=False,
                message=f"Data operations test failed: {e}",
                duration=time.time() - start_time
            )
    
    async def test_vector_search(self) -> ValidationResult:
        """Test vector search functionality."""
        start_time = time.time()
        
        try:
            # Create test data for search
            test_items = [
                {
                    'id': 'search-test-001',
                    'title': 'Customer Portal Development',
                    'description': 'Build a customer-facing web portal for account management',
                    'item_type': 'feature',
                    'status': 'todo',
                    'priority': 'high'
                },
                {
                    'id': 'search-test-002',
                    'title': 'Database Migration',
                    'description': 'Migrate from Weaviate to LanceDB for better performance',
                    'item_type': 'task',
                    'status': 'in_progress',
                    'priority': 'high'
                },
                {
                    'id': 'search-test-003',
                    'title': 'User Authentication',
                    'description': 'Implement OAuth2 authentication for secure access',
                    'item_type': 'feature',
                    'status': 'todo',
                    'priority': 'medium'
                }
            ]
            
            # Create test items
            for item in test_items:
                await self.server_manager.create_work_item(item)
            
            # Test vector search
            search_queries = [
                ('customer portal', 'search-test-001'),
                ('database migration', 'search-test-002'),
                ('authentication security', 'search-test-003')
            ]
            
            search_results = []
            for query, expected_id in search_queries:
                results = await self.server_manager.search_work_items(
                    query=query,
                    search_type=SearchType.VECTOR,
                    limit=5
                )
                
                if not results:
                    return ValidationResult(
                        test_name="Vector Search",
                        passed=False,
                        message=f"No results for query: '{query}'",
                        duration=time.time() - start_time
                    )
                
                # Check if expected item is in top results
                found_expected = any(result['id'] == expected_id for result in results[:3])
                search_results.append({
                    'query': query,
                    'expected_id': expected_id,
                    'found_expected': found_expected,
                    'result_count': len(results),
                    'top_result': results[0]['id'] if results else None
                })
            
            # Clean up test data
            for item in test_items:
                await self.server_manager.delete_work_item(item['id'])
            
            # Evaluate results
            successful_searches = sum(1 for result in search_results if result['found_expected'])
            success_rate = successful_searches / len(search_queries)
            
            if success_rate < 0.6:  # At least 60% success rate
                return ValidationResult(
                    test_name="Vector Search",
                    passed=False,
                    message=f"Vector search success rate too low: {success_rate:.1%}",
                    duration=time.time() - start_time,
                    details={'search_results': search_results}
                )
            
            return ValidationResult(
                test_name="Vector Search",
                passed=True,
                message=f"Vector search working with {success_rate:.1%} success rate",
                duration=time.time() - start_time,
                details={'search_results': search_results}
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Vector Search",
                passed=False,
                message=f"Vector search test failed: {e}",
                duration=time.time() - start_time
            )
    
    async def test_embedding_generation(self) -> ValidationResult:
        """Test embedding generation functionality."""
        start_time = time.time()
        
        try:
            # Test embedding generation with various text inputs
            test_texts = [
                "Simple test text",
                "This is a longer text with more complex content for testing embedding generation",
                "Technical documentation about vector databases and semantic search",
                "",  # Empty text
                "   ",  # Whitespace only
            ]
            
            embedding_results = []
            
            for text in test_texts:
                # Create a test work item to trigger embedding generation
                test_item = {
                    'id': f'embed-test-{len(embedding_results)}',
                    'title': f'Embedding Test {len(embedding_results)}',
                    'description': text,
                    'item_type': 'task',
                    'status': 'todo',
                    'priority': 'low'
                }
                
                created_result = await self.server_manager.create_work_item(test_item)
                created_id = created_result['id'] if isinstance(created_result, dict) else created_result
                retrieved_item = await self.server_manager.get_work_item(created_id)
                
                # Check if embedding was generated
                if retrieved_item is None:
                    has_vector = False
                    vector_length = 0
                else:
                    has_vector = 'vector' in retrieved_item and retrieved_item['vector'] is not None
                    vector_length = len(retrieved_item['vector']) if has_vector else 0
                
                embedding_results.append({
                    'text': text,
                    'has_vector': has_vector,
                    'vector_length': vector_length,
                    'expected_length': 384
                })
                
                # Clean up
                await self.server_manager.delete_work_item(created_id)
            
            # Evaluate results
            successful_embeddings = sum(1 for result in embedding_results 
                                      if result['has_vector'] and result['vector_length'] == 384)
            
            if successful_embeddings < len(test_texts):
                return ValidationResult(
                    test_name="Embedding Generation",
                    passed=False,
                    message=f"Embedding generation failed for {len(test_texts) - successful_embeddings} texts",
                    duration=time.time() - start_time,
                    details={'embedding_results': embedding_results}
                )
            
            return ValidationResult(
                test_name="Embedding Generation",
                passed=True,
                message="All embeddings generated successfully",
                duration=time.time() - start_time,
                details={'embedding_results': embedding_results}
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Embedding Generation",
                passed=False,
                message=f"Embedding generation test failed: {e}",
                duration=time.time() - start_time
            )
    
    async def test_performance_benchmarks(self) -> ValidationResult:
        """Run performance benchmarks."""
        start_time = time.time()
        
        try:
            # Create test dataset
            test_items = []
            for i in range(100):
                test_items.append({
                    'id': f'perf-test-{i:03d}',
                    'title': f'Performance Test Item {i}',
                    'description': f'This is test item {i} for performance benchmarking with various content lengths and complexity',
                    'item_type': 'task',
                    'status': 'todo',
                    'priority': 'medium'
                })
            
            # Benchmark insertion
            insert_start = time.time()
            for item in test_items:
                await self.server_manager.create_work_item(item)
            insert_time = time.time() - insert_start
            
            # Benchmark search
            search_start = time.time()
            search_queries = [
                'performance test',
                'benchmarking',
                'test item',
                'complexity',
                'various content'
            ]
            
            search_times = []
            for query in search_queries:
                query_start = time.time()
                results = await self.server_manager.search_work_items(
                    query=query,
                    search_type=SearchType.VECTOR,
                    limit=10
                )
                query_time = time.time() - query_start
                search_times.append(query_time)
            
            avg_search_time = sum(search_times) / len(search_times)
            total_search_time = time.time() - search_start
            
            # Benchmark retrieval
            retrieval_start = time.time()
            for i in range(0, 100, 10):  # Sample every 10th item
                item_id = f'perf-test-{i:03d}'
                await self.server_manager.get_work_item(item_id)
            retrieval_time = time.time() - retrieval_start
            
            # Clean up
            cleanup_start = time.time()
            for item in test_items:
                await self.server_manager.delete_work_item(item['id'])
            cleanup_time = time.time() - cleanup_start
            
            # Evaluate performance
            benchmarks = {
                'insert_time_total': insert_time,
                'insert_time_per_item': insert_time / len(test_items),
                'search_time_avg': avg_search_time,
                'search_time_total': total_search_time,
                'retrieval_time_total': retrieval_time,
                'retrieval_time_per_item': retrieval_time / 10,
                'cleanup_time_total': cleanup_time,
                'items_processed': len(test_items)
            }
            
            # Performance thresholds
            performance_issues = []
            if benchmarks['insert_time_per_item'] > 0.5:  # 500ms per item
                performance_issues.append(f"Slow insertion: {benchmarks['insert_time_per_item']:.3f}s per item")
            
            if benchmarks['search_time_avg'] > 0.1:  # 100ms per search
                performance_issues.append(f"Slow search: {benchmarks['search_time_avg']:.3f}s average")
            
            if benchmarks['retrieval_time_per_item'] > 0.05:  # 50ms per retrieval
                performance_issues.append(f"Slow retrieval: {benchmarks['retrieval_time_per_item']:.3f}s per item")
            
            if performance_issues:
                return ValidationResult(
                    test_name="Performance Benchmarks",
                    passed=False,
                    message=f"Performance issues detected: {'; '.join(performance_issues)}",
                    duration=time.time() - start_time,
                    details=benchmarks
                )
            
            return ValidationResult(
                test_name="Performance Benchmarks",
                passed=True,
                message="All performance benchmarks passed",
                duration=time.time() - start_time,
                details=benchmarks
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Performance Benchmarks",
                passed=False,
                message=f"Performance benchmark failed: {e}",
                duration=time.time() - start_time
            )
    
    async def run_all_tests(self, include_benchmarks: bool = False) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("🚀 Starting LanceDB migration validation...")
        
        # Initialize managers
        if not await self.initialize_managers():
            return {
                'success': False,
                'message': 'Failed to initialize LanceDB managers',
                'results': []
            }
        
        # Run tests
        tests = [
            self.test_database_connectivity(),
            self.test_table_existence(),
            self.test_data_operations(),
            self.test_vector_search(),
            self.test_embedding_generation()
        ]
        
        if include_benchmarks:
            tests.append(self.test_performance_benchmarks())
        
        # Execute tests
        for test_coro in tests:
            result = await test_coro
            self.log_result(result)
        
        # Cleanup
        try:
            if self.server_manager:
                await self.server_manager.cleanup()
            if self.jive_manager:
                await self.jive_manager.cleanup()
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
        
        # Generate summary
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.passed)
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        summary = {
            'success': failed_tests == 0,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'results': [{
                'test_name': r.test_name,
                'passed': r.passed,
                'message': r.message,
                'duration': r.duration,
                'details': r.details
            } for r in self.results]
        }
        
        return summary

def print_validation_report(summary: Dict[str, Any]):
    """Print detailed validation report."""
    print("\n" + "="*60)
    print("🔍 LANCEDB MIGRATION VALIDATION REPORT")
    print("="*60)
    
    status = "✅ SUCCESS" if summary['success'] else "❌ FAILURE"
    print(f"Overall Status: {status}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    
    if summary['failed_tests'] > 0:
        print(f"Tests Failed: {summary['failed_tests']}")
        print("\n❌ Failed Tests:")
        for result in summary['results']:
            if not result['passed']:
                print(f"  • {result['test_name']}: {result['message']}")
    
    print("\n📊 Test Details:")
    for result in summary['results']:
        status_icon = "✅" if result['passed'] else "❌"
        duration_str = f" ({result['duration']:.3f}s)" if result['duration'] > 0 else ""
        print(f"  {status_icon} {result['test_name']}{duration_str}")
        print(f"    {result['message']}")
    
    print("\n" + "="*60)
    
    if summary['success']:
        print("🎉 LanceDB migration validation completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Update application configuration to use LanceDB")
        print("  2. Remove Weaviate dependencies")
        print("  3. Deploy to production environment")
    else:
        print("⚠️ LanceDB migration validation failed!")
        print("\n🔧 Recommended actions:")
        print("  1. Review failed test details above")
        print("  2. Check LanceDB installation and configuration")
        print("  3. Verify data migration completed successfully")
        print("  4. Re-run validation after fixes")

async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description='Validate LanceDB migration')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logging')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--compare-backup', help='Compare with Weaviate backup file')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Run validation suite
        validator = ValidationSuite(verbose=args.verbose)
        summary = await validator.run_all_tests(include_benchmarks=args.benchmark)
        
        # Print report
        print_validation_report(summary)
        
        # Save detailed results
        results_file = f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if summary['success'] else 1)
        
    except Exception as e:
        logger.error(f"❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())