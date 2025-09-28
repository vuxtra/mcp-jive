#!/usr/bin/env python3
"""Comprehensive E2E Test Runner for MCP Jive.

This script executes all E2E tests and generates detailed reports.
It can be used in CI/CD pipelines or for local testing.
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "tests"))

from tests.e2e.test_e2e_automation import E2ETestRunner
from tests.e2e.run_e2e_tests import E2ETestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveE2ERunner:
    """Comprehensive E2E test runner with reporting and CI/CD integration."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.start_time = None
        self.end_time = None
        self.results = {
            "summary": {},
            "test_phases": {},
            "pytest_results": {},
            "performance_metrics": {},
            "errors": []
        }
    
    async def run_automated_e2e_tests(self) -> Dict[str, Any]:
        """Run the automated E2E test suite."""
        logger.info("Starting automated E2E test suite...")
        
        try:
            test_suite = E2ETestSuite()
            results = await test_suite.run_all_phases()
            
            self.results["test_phases"] = results
            logger.info(f"Automated E2E tests completed: {results['summary']}")
            return results
            
        except Exception as e:
            error_msg = f"Automated E2E tests failed: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return {"status": "failed", "error": str(e)}
    
    def run_pytest_e2e_tests(self) -> Dict[str, Any]:
        """Run pytest-based E2E tests."""
        logger.info("Running pytest E2E tests...")
        
        try:
            # Run pytest with E2E markers
            cmd = [
                "python", "-m", "pytest",
                "tests/e2e/",
                "-m", "e2e",
                "--verbose",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.output_dir}/pytest_e2e_report.json",
                "--html", f"{self.output_dir}/pytest_e2e_report.html",
                "--self-contained-html"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            pytest_results = {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Try to load JSON report if available
            json_report_path = self.output_dir / "pytest_e2e_report.json"
            if json_report_path.exists():
                with open(json_report_path) as f:
                    pytest_results["detailed_report"] = json.load(f)
            
            self.results["pytest_results"] = pytest_results
            logger.info(f"Pytest E2E tests completed with return code: {result.returncode}")
            return pytest_results
            
        except Exception as e:
            error_msg = f"Pytest E2E tests failed: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return {"success": False, "error": str(e)}
    
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance-focused E2E tests."""
        logger.info("Running performance E2E tests...")
        
        try:
            runner = E2ETestRunner()
            await runner.setup()
            
            performance_metrics = {
                "response_times": [],
                "throughput": {},
                "resource_usage": {}
            }
            
            # Test work item creation performance
            start_time = time.time()
            for i in range(10):
                await runner.call_mcp_tool(
                    "jive_manage_work_item",
                    {
                        "action": "create",
                        "type": "task",
                        "title": f"Performance Test Task {i}",
                        "description": "Performance testing task"
                    }
                )
            end_time = time.time()
            
            performance_metrics["response_times"].append({
                "operation": "bulk_create_tasks",
                "count": 10,
                "total_time": end_time - start_time,
                "avg_time_per_operation": (end_time - start_time) / 10
            })
            
            # Test search performance
            start_time = time.time()
            await runner.call_mcp_tool(
                "jive_search_content",
                {
                    "query": "Performance Test",
                    "limit": 50
                }
            )
            end_time = time.time()
            
            performance_metrics["response_times"].append({
                "operation": "search_content",
                "query_time": end_time - start_time
            })
            
            await runner.teardown()
            
            self.results["performance_metrics"] = performance_metrics
            logger.info("Performance E2E tests completed")
            return performance_metrics
            
        except Exception as e:
            error_msg = f"Performance E2E tests failed: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return {"status": "failed", "error": str(e)}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        logger.info("Generating comprehensive test report...")
        
        # Calculate summary statistics
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        # From automated tests
        if "test_phases" in self.results and "summary" in self.results["test_phases"]:
            phase_summary = self.results["test_phases"]["summary"]
            total_tests += phase_summary.get("total_tests", 0)
            passed_tests += phase_summary.get("passed_tests", 0)
            failed_tests += phase_summary.get("failed_tests", 0)
        
        # From pytest results
        if "pytest_results" in self.results and "detailed_report" in self.results["pytest_results"]:
            pytest_report = self.results["pytest_results"]["detailed_report"]
            if "summary" in pytest_report:
                total_tests += pytest_report["summary"].get("total", 0)
                passed_tests += pytest_report["summary"].get("passed", 0)
                failed_tests += pytest_report["summary"].get("failed", 0)
        
        # Calculate execution time
        execution_time = None
        if self.start_time and self.end_time:
            execution_time = self.end_time - self.start_time
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_status": "PASSED" if failed_tests == 0 and total_tests > 0 else "FAILED",
            "errors_count": len(self.results["errors"])
        }
        
        self.results["summary"] = summary
        
        # Save detailed report
        report_file = self.output_dir / "comprehensive_e2e_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate human-readable report
        self.generate_human_readable_report()
        
        logger.info(f"Comprehensive report saved to {report_file}")
        return self.results
    
    def generate_human_readable_report(self):
        """Generate a human-readable markdown report."""
        report_file = self.output_dir / "e2e_test_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# E2E Test Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            summary = self.results.get("summary", {})
            f.write("## Summary\n\n")
            f.write(f"- **Overall Status**: {summary.get('overall_status', 'UNKNOWN')}\n")
            f.write(f"- **Total Tests**: {summary.get('total_tests', 0)}\n")
            f.write(f"- **Passed**: {summary.get('passed_tests', 0)}\n")
            f.write(f"- **Failed**: {summary.get('failed_tests', 0)}\n")
            f.write(f"- **Success Rate**: {summary.get('success_rate', 0):.1f}%\n")
            if summary.get('execution_time_seconds'):
                f.write(f"- **Execution Time**: {summary['execution_time_seconds']:.2f} seconds\n")
            f.write("\n")
            
            # Test Phases
            if "test_phases" in self.results:
                f.write("## Automated Test Phases\n\n")
                phases = self.results["test_phases"].get("phases", {})
                for phase_name, phase_data in phases.items():
                    status = "✅" if phase_data.get("success", False) else "❌"
                    f.write(f"### {status} {phase_name}\n")
                    f.write(f"- **Status**: {phase_data.get('status', 'Unknown')}\n")
                    if "tests_run" in phase_data:
                        f.write(f"- **Tests Run**: {phase_data['tests_run']}\n")
                    if "execution_time" in phase_data:
                        f.write(f"- **Execution Time**: {phase_data['execution_time']:.2f}s\n")
                    f.write("\n")
            
            # Performance Metrics
            if "performance_metrics" in self.results:
                f.write("## Performance Metrics\n\n")
                metrics = self.results["performance_metrics"]
                if "response_times" in metrics:
                    for metric in metrics["response_times"]:
                        f.write(f"- **{metric.get('operation', 'Unknown')}**: ")
                        if "avg_time_per_operation" in metric:
                            f.write(f"{metric['avg_time_per_operation']:.3f}s avg\n")
                        elif "query_time" in metric:
                            f.write(f"{metric['query_time']:.3f}s\n")
                f.write("\n")
            
            # Errors
            if self.results.get("errors"):
                f.write("## Errors\n\n")
                for i, error in enumerate(self.results["errors"], 1):
                    f.write(f"{i}. {error}\n")
                f.write("\n")
        
        logger.info(f"Human-readable report saved to {report_file}")
    
    async def run_all_tests(self, include_performance: bool = True) -> Dict[str, Any]:
        """Run all E2E tests and generate comprehensive report."""
        self.start_time = time.time()
        logger.info("Starting comprehensive E2E test execution...")
        
        try:
            # Run automated E2E tests
            await self.run_automated_e2e_tests()
            
            # Run pytest E2E tests
            self.run_pytest_e2e_tests()
            
            # Run performance tests if requested
            if include_performance:
                await self.run_performance_tests()
            
        except Exception as e:
            logger.error(f"Error during test execution: {str(e)}")
            self.results["errors"].append(f"Test execution error: {str(e)}")
        
        finally:
            self.end_time = time.time()
            return self.generate_comprehensive_report()


def main():
    """Main entry point for the E2E test runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive E2E tests for MCP Jive")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("test_results"),
        help="Output directory for test results"
    )
    parser.add_argument(
        "--no-performance",
        action="store_true",
        help="Skip performance tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure we're in the project root
    os.chdir(project_root)
    
    async def run_tests():
        runner = ComprehensiveE2ERunner(args.output_dir)
        results = await runner.run_all_tests(include_performance=not args.no_performance)
        
        # Print summary
        summary = results.get("summary", {})
        print("\n" + "="*60)
        print("E2E TEST EXECUTION SUMMARY")
        print("="*60)
        print(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        if summary.get('execution_time_seconds'):
            print(f"Execution Time: {summary['execution_time_seconds']:.2f} seconds")
        print(f"\nDetailed reports saved to: {args.output_dir}")
        print("="*60)
        
        # Exit with appropriate code
        exit_code = 0 if summary.get('overall_status') == 'PASSED' else 1
        sys.exit(exit_code)
    
    # Run the async function
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()