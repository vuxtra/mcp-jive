#!/usr/bin/env python3
"""E2E Test Runner for MCP Jive.

This script runs the complete E2E test suite and generates detailed reports.
It can be used for CI/CD pipelines and manual testing.
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from test_e2e_automation import E2ETestRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('e2e_test_results.log')
    ]
)
logger = logging.getLogger(__name__)


class E2ETestSuite:
    """Complete E2E test suite runner."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.results: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "errors": [],
            "summary": {}
        }
        self.runner: Optional[E2ETestRunner] = None
        
    async def setup_environment(self) -> bool:
        """Setup the test environment."""
        try:
            logger.info("Setting up E2E test environment...")
            
            # Initialize test runner
            self.runner = E2ETestRunner()
            await self.runner.setup()
            
            logger.info("E2E test environment setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            self.results["errors"].append({
                "phase": "setup",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
            
    async def cleanup_environment(self):
        """Cleanup the test environment."""
        try:
            if self.runner:
                await self.runner.teardown()
            logger.info("E2E test environment cleanup complete")
        except Exception as e:
            logger.error(f"Failed to cleanup test environment: {e}")
            
    async def run_test_phase(self, phase_name: str, test_func) -> Dict[str, Any]:
        """Run a single test phase and capture results."""
        phase_result = {
            "phase": phase_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration": 0,
            "status": "failed",
            "error": None,
            "details": {}
        }
        
        start_time = time.time()
        
        try:
            logger.info(f"Running {phase_name}...")
            
            # Execute the test function
            result = await test_func()
            
            phase_result["status"] = "passed"
            phase_result["details"] = result or {}
            
            logger.info(f"{phase_name} - PASSED")
            
        except Exception as e:
            phase_result["status"] = "failed"
            phase_result["error"] = str(e)
            
            logger.error(f"{phase_name} - FAILED: {e}")
            
        finally:
            end_time = time.time()
            phase_result["end_time"] = datetime.now().isoformat()
            phase_result["duration"] = end_time - start_time
            
        return phase_result
        
    async def test_phase_1_basic_work_item_management(self) -> Dict[str, Any]:
        """Test Phase 1: Basic Work Item Management."""
        results = {}
        
        # Test 1.1: Create Initiative
        initiative_id = await self.runner.create_work_item(
            item_type="initiative",
            title="E-commerce Platform Modernization",
            description="Modernize our legacy e-commerce platform to improve performance, scalability, and user experience."
        )
        results["initiative_created"] = initiative_id is not None
        results["initiative_id"] = initiative_id
        
        # Test 1.2: Create Epic Under Initiative
        epic_id = await self.runner.create_work_item(
            item_type="epic",
            title="User Authentication System",
            description="Implement secure, scalable user authentication with multi-factor authentication.",
            parent_id=initiative_id
        )
        results["epic_created"] = epic_id is not None
        results["epic_id"] = epic_id
        
        # Test 1.3: Create Features Under Epic
        features = [
            ("Multi-Factor Authentication", "Implement SMS and email-based 2FA"),
            ("Social Login Integration", "Add Google, Facebook, and GitHub OAuth"),
            ("Role-Based Access Control", "Implement user roles and permissions")
        ]
        
        feature_ids = []
        for title, description in features:
            feature_id = await self.runner.create_work_item(
                item_type="feature",
                title=title,
                description=description,
                parent_id=epic_id
            )
            feature_ids.append(feature_id)
            
        results["features_created"] = len(feature_ids) == 3
        results["feature_ids"] = feature_ids
        
        # Test 1.4: Create Stories Under Features
        if feature_ids:
            mfa_feature_id = feature_ids[0]
            stories = [
                "As a user, I want to enable 2FA via SMS",
                "As a user, I want to enable 2FA via email",
                "As an admin, I want to enforce 2FA for all users"
            ]
            
            story_ids = []
            for story_title in stories:
                story_id = await self.runner.create_work_item(
                    item_type="story",
                    title=story_title,
                    description=f"User story: {story_title}",
                    parent_id=mfa_feature_id
                )
                story_ids.append(story_id)
                
            results["stories_created"] = len(story_ids) == 3
            results["story_ids"] = story_ids
            
        return results
        
    async def test_phase_2_work_item_queries(self) -> Dict[str, Any]:
        """Test Phase 2: Work Item Queries and Management."""
        results = {}
        
        # Test 2.1: Search for work items
        search_result = await self.runner.search_content(
            query="authentication security",
            search_type="semantic"
        )
        results["search_executed"] = search_result is not None
        results["search_results_count"] = len(search_result.get("results", []))
        
        # Test 2.2: Get work item details
        if self.runner.created_items:
            item_id = self.runner.created_items[0]
            item_details = await self.runner.get_work_item(item_id)
            results["item_retrieval"] = item_details is not None
            results["item_has_title"] = "title" in item_details
            
        return results
        
    async def test_phase_3_hierarchy_and_dependencies(self) -> Dict[str, Any]:
        """Test Phase 3: Hierarchy and Dependencies."""
        results = {}
        
        # Create test hierarchy
        parent_id = await self.runner.create_work_item(
            item_type="epic",
            title="Test Epic for Hierarchy",
            description="Epic to test hierarchy functionality"
        )
        
        child_id = await self.runner.create_work_item(
            item_type="feature",
            title="Test Feature",
            description="Feature for hierarchy testing",
            parent_id=parent_id
        )
        
        # Test hierarchy retrieval
        hierarchy = await self.runner.get_hierarchy(parent_id, "children")
        results["hierarchy_retrieved"] = hierarchy is not None
        results["has_children"] = len(hierarchy.get("children", [])) > 0
        
        # Test full hierarchy
        full_hierarchy = await self.runner.get_hierarchy(parent_id, "full_hierarchy")
        results["full_hierarchy_retrieved"] = full_hierarchy is not None
        
        return results
        
    async def test_phase_4_workflow_execution(self) -> Dict[str, Any]:
        """Test Phase 4: Workflow Execution."""
        results = {}
        
        # Create task for execution
        task_id = await self.runner.create_work_item(
            item_type="task",
            title="Test Task for Execution",
            description="Task to test workflow execution"
        )
        
        # Test execution
        execution_result = await self.runner.execute_work_item(
            work_item_id=task_id,
            execution_mode="validation_only"
        )
        results["execution_started"] = execution_result is not None
        
        # Test status check
        status_result = await self.runner.call_tool("jive_execute_work_item", {
            "work_item_id": task_id,
            "action": "status"
        })
        results["status_checked"] = status_result is not None
        
        return results
        
    async def test_phase_5_progress_tracking(self) -> Dict[str, Any]:
        """Test Phase 5: Progress Tracking."""
        results = {}
        
        # Create task for progress tracking
        task_id = await self.runner.create_work_item(
            item_type="task",
            title="Task for Progress Tracking",
            description="Task to test progress tracking"
        )
        
        # Test progress tracking
        progress_result = await self.runner.track_progress(
            work_item_id=task_id,
            progress_percentage=75,
            status="in_progress"
        )
        results["progress_tracked"] = progress_result is not None
        
        # Test progress report
        report_result = await self.runner.call_tool("jive_track_progress", {
            "action": "get_report",
            "work_item_id": task_id
        })
        results["report_generated"] = report_result is not None
        
        return results
        
    async def test_phase_6_data_synchronization(self) -> Dict[str, Any]:
        """Test Phase 6: Data Synchronization."""
        results = {}
        
        # Test data sync
        sync_result = await self.runner.sync_data("file_to_db")
        results["sync_executed"] = sync_result is not None
        
        # Test sync status
        status_result = await self.runner.call_tool("jive_sync_data", {
            "action": "status"
        })
        results["sync_status_checked"] = status_result is not None
        
        return results
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all E2E test phases."""
        self.results["start_time"] = datetime.now().isoformat()
        start_time = time.time()
        
        # Define test phases
        test_phases = [
            ("Phase 1: Basic Work Item Management", self.test_phase_1_basic_work_item_management),
            ("Phase 2: Work Item Queries", self.test_phase_2_work_item_queries),
            ("Phase 3: Hierarchy and Dependencies", self.test_phase_3_hierarchy_and_dependencies),
            ("Phase 4: Workflow Execution", self.test_phase_4_workflow_execution),
            ("Phase 5: Progress Tracking", self.test_phase_5_progress_tracking),
            ("Phase 6: Data Synchronization", self.test_phase_6_data_synchronization)
        ]
        
        # Setup environment
        if not await self.setup_environment():
            return self.results
            
        try:
            # Run each test phase
            for phase_name, test_func in test_phases:
                phase_result = await self.run_test_phase(phase_name, test_func)
                self.results["test_results"].append(phase_result)
                
                if phase_result["status"] == "passed":
                    self.results["passed_tests"] += 1
                else:
                    self.results["failed_tests"] += 1
                    
                self.results["total_tests"] += 1
                
        finally:
            # Cleanup environment
            await self.cleanup_environment()
            
        # Calculate final results
        end_time = time.time()
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = end_time - start_time
        
        # Generate summary
        self.results["summary"] = {
            "success_rate": (self.results["passed_tests"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0,
            "total_duration": self.results["duration"],
            "average_test_duration": self.results["duration"] / self.results["total_tests"] if self.results["total_tests"] > 0 else 0,
            "status": "PASSED" if self.results["failed_tests"] == 0 else "FAILED"
        }
        
        return self.results
        
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a detailed test report."""
        report = []
        report.append("# MCP Jive E2E Test Report")
        report.append(f"**Generated**: {datetime.now().isoformat()}")
        report.append(f"**Duration**: {self.results['duration']:.2f} seconds")
        report.append("")
        
        # Summary
        summary = self.results["summary"]
        report.append("## Summary")
        report.append(f"- **Status**: {summary['status']}")
        report.append(f"- **Success Rate**: {summary['success_rate']:.1f}%")
        report.append(f"- **Total Tests**: {self.results['total_tests']}")
        report.append(f"- **Passed**: {self.results['passed_tests']}")
        report.append(f"- **Failed**: {self.results['failed_tests']}")
        report.append("")
        
        # Test Results
        report.append("## Test Results")
        for test_result in self.results["test_results"]:
            status_icon = "✅" if test_result["status"] == "passed" else "❌"
            report.append(f"### {status_icon} {test_result['phase']}")
            report.append(f"- **Status**: {test_result['status'].upper()}")
            report.append(f"- **Duration**: {test_result['duration']:.2f} seconds")
            
            if test_result["error"]:
                report.append(f"- **Error**: {test_result['error']}")
                
            if test_result["details"]:
                report.append("- **Details**:")
                for key, value in test_result["details"].items():
                    report.append(f"  - {key}: {value}")
                    
            report.append("")
            
        # Errors
        if self.results["errors"]:
            report.append("## Errors")
            for error in self.results["errors"]:
                report.append(f"- **{error['phase']}**: {error['error']} ({error['timestamp']})")
            report.append("")
            
        report_text = "\n".join(report)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
            
        return report_text
        
    def save_json_results(self, output_file: str):
        """Save results as JSON for CI/CD integration."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"JSON results saved to {output_file}")


async def main():
    """Main entry point for E2E test runner."""
    parser = argparse.ArgumentParser(description="MCP Jive E2E Test Runner")
    parser.add_argument("--output", "-o", help="Output file for test report")
    parser.add_argument("--json", help="Output file for JSON results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Run E2E tests
    test_suite = E2ETestSuite()
    
    logger.info("Starting MCP Jive E2E Test Suite...")
    results = await test_suite.run_all_tests()
    
    # Generate and display report
    report = test_suite.generate_report(args.output)
    print(report)
    
    # Save JSON results if requested
    if args.json:
        test_suite.save_json_results(args.json)
        
    # Exit with appropriate code
    exit_code = 0 if results["summary"]["status"] == "PASSED" else 1
    logger.info(f"E2E Test Suite completed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)