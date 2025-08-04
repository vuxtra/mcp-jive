#!/usr/bin/env python3
"""
Comprehensive Test Runner for Consolidated MCP Jive Tools

This script executes the comprehensive test plan in phases and generates
detailed reports on the validation of all 32 legacy tool capabilities.

Usage:
    python run_comprehensive_tests.py [phase] [options]
    
Phases:
    unit        - Run individual tool tests (TC-001 to TC-028)
    integration - Run cross-tool workflow tests (TC-029 to TC-030)
    performance - Run performance and stress tests (TC-031 to TC-032)
    all         - Run all test phases
    
Options:
    --verbose   - Detailed output
    --report    - Generate HTML report
    --json      - Generate JSON report
    --coverage  - Include code coverage
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Test configuration
TEST_PHASES = {
    "unit": {
        "name": "Unit Testing",
        "description": "Individual tool functionality tests",
        "test_pattern": "not (tc029 or tc030 or tc031 or tc032)",
        "expected_tests": 28,
        "timeout": 300  # 5 minutes
    },
    "integration": {
        "name": "Integration Testing",
        "description": "Cross-tool workflow tests",
        "test_pattern": "tc029 or tc030",
        "expected_tests": 2,
        "timeout": 600  # 10 minutes
    },
    "performance": {
        "name": "Performance Testing",
        "description": "Performance and stress tests",
        "test_pattern": "tc031 or tc032",
        "markers": "slow",
        "expected_tests": 2,
        "timeout": 1800  # 30 minutes
    }
}

LEGACY_TOOL_MAPPING = {
    "UnifiedWorkItemTool": [
        "create_work_item",
        "update_work_item",
        "delete_work_item",
        "assign_work_item",
        "change_work_item_status"
    ],
    "UnifiedRetrievalTool": [
        "get_work_item_by_id",
        "list_work_items",
        "filter_work_items",
        "get_work_item_details"
    ],
    "UnifiedSearchTool": [
        "search_work_items",
        "semantic_search",
        "full_text_search"
    ],
    "UnifiedHierarchyTool": [
        "get_parent_items",
        "get_child_items",
        "create_relationship",
        "remove_relationship",
        "get_dependencies",
        "update_hierarchy"
    ],
    "UnifiedExecutionTool": [
        "execute_workflow",
        "check_execution_status",
        "cancel_execution",
        "retry_execution",
        "validate_execution"
    ],
    "UnifiedProgressTool": [
        "update_progress",
        "get_progress_report",
        "track_milestones",
        "generate_analytics"
    ],
    "UnifiedStorageTool": [
        "backup_data",
        "restore_data",
        "sync_external",
        "export_data",
        "import_data"
    ]
}


class TestRunner:
    """Manages comprehensive test execution and reporting."""
    
    def __init__(self, verbose: bool = False, generate_report: bool = False, 
                 json_report: bool = False, coverage: bool = False):
        self.verbose = verbose
        self.generate_report = generate_report
        self.json_report = json_report
        self.coverage = coverage
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        
        if level == "ERROR":
            print(f"\033[91m{prefix} {message}\033[0m")  # Red
        elif level == "SUCCESS":
            print(f"\033[92m{prefix} {message}\033[0m")  # Green
        elif level == "WARNING":
            print(f"\033[93m{prefix} {message}\033[0m")  # Yellow
        else:
            print(f"{prefix} {message}")
    
    def run_pytest_phase(self, phase: str) -> Dict[str, Any]:
        """Run a specific test phase using pytest."""
        phase_config = TEST_PHASES[phase]
        self.log(f"Starting {phase_config['name']}...")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest", "-v"]
        
        # Add test pattern
        if "test_pattern" in phase_config:
            cmd.extend(["-k", phase_config["test_pattern"]])
        
        # Add markers
        if "markers" in phase_config:
            cmd.extend(["-m", phase_config["markers"]])
        
        # Add coverage if requested
        if self.coverage:
            cmd.extend(["--cov=src/mcp_jive/tools/consolidated", "--cov-report=html"])
        
        # Add JSON output
        json_file = f"test_results_{phase}.json"
        cmd.extend(["--json-report", f"--json-report-file={json_file}"])
        
        # Add test file
        cmd.append("tests/test_consolidated_tools_comprehensive.py")
        
        # Set timeout
        timeout = phase_config.get("timeout", 300)
        
        try:
            self.log(f"Executing: {' '.join(cmd)}")
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            phase_result = {
                "phase": phase,
                "name": phase_config["name"],
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Try to load JSON report
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                        phase_result["detailed_results"] = json_data
                        phase_result["tests_run"] = json_data.get("summary", {}).get("total", 0)
                        phase_result["tests_passed"] = json_data.get("summary", {}).get("passed", 0)
                        phase_result["tests_failed"] = json_data.get("summary", {}).get("failed", 0)
                        phase_result["tests_skipped"] = json_data.get("summary", {}).get("skipped", 0)
                except Exception as e:
                    self.log(f"Could not parse JSON report: {e}", "WARNING")
            
            if phase_result["success"]:
                self.log(f"{phase_config['name']} completed successfully in {duration:.2f}s", "SUCCESS")
            else:
                self.log(f"{phase_config['name']} failed after {duration:.2f}s", "ERROR")
                if self.verbose:
                    self.log(f"STDOUT: {result.stdout}")
                    self.log(f"STDERR: {result.stderr}")
            
            return phase_result
            
        except subprocess.TimeoutExpired:
            self.log(f"{phase_config['name']} timed out after {timeout}s", "ERROR")
            return {
                "phase": phase,
                "name": phase_config["name"],
                "duration": timeout,
                "return_code": -1,
                "success": False,
                "error": "Timeout"
            }
        except Exception as e:
            self.log(f"{phase_config['name']} failed with exception: {e}", "ERROR")
            return {
                "phase": phase,
                "name": phase_config["name"],
                "duration": 0,
                "return_code": -1,
                "success": False,
                "error": str(e)
            }
    
    def run_phase(self, phase: str) -> Dict[str, Any]:
        """Run a specific test phase."""
        if phase not in TEST_PHASES:
            raise ValueError(f"Unknown phase: {phase}. Available: {list(TEST_PHASES.keys())}")
        
        return self.run_pytest_phase(phase)
    
    def run_all_phases(self) -> Dict[str, Any]:
        """Run all test phases in sequence."""
        self.start_time = datetime.now()
        self.log("Starting comprehensive test execution...")
        
        all_results = {
            "start_time": self.start_time.isoformat(),
            "phases": {},
            "summary": {
                "total_phases": len(TEST_PHASES),
                "passed_phases": 0,
                "failed_phases": 0,
                "total_duration": 0
            }
        }
        
        for phase_name in TEST_PHASES.keys():
            self.log(f"\n{'='*60}")
            self.log(f"PHASE: {TEST_PHASES[phase_name]['name'].upper()}")
            self.log(f"{'='*60}")
            
            phase_result = self.run_phase(phase_name)
            all_results["phases"][phase_name] = phase_result
            
            if phase_result["success"]:
                all_results["summary"]["passed_phases"] += 1
            else:
                all_results["summary"]["failed_phases"] += 1
            
            all_results["summary"]["total_duration"] += phase_result.get("duration", 0)
        
        self.end_time = datetime.now()
        all_results["end_time"] = self.end_time.isoformat()
        all_results["summary"]["total_duration"] = (self.end_time - self.start_time).total_seconds()
        
        self.results = all_results
        return all_results
    
    def generate_legacy_capability_report(self) -> Dict[str, Any]:
        """Generate report on legacy capability preservation."""
        capability_report = {
            "total_legacy_tools": sum(len(tools) for tools in LEGACY_TOOL_MAPPING.values()),
            "unified_tools": len(LEGACY_TOOL_MAPPING),
            "capability_mapping": {},
            "validation_status": {}
        }
        
        for unified_tool, legacy_tools in LEGACY_TOOL_MAPPING.items():
            capability_report["capability_mapping"][unified_tool] = {
                "legacy_tools_replaced": legacy_tools,
                "count": len(legacy_tools),
                "test_coverage": "pending"  # Would be filled by actual test results
            }
        
        return capability_report
    
    def generate_html_report(self) -> str:
        """Generate HTML test report."""
        if not self.results:
            return "No test results available"
        
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Jive Consolidated Tools Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .phase { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background: #d4edda; border-color: #c3e6cb; }
        .failure { background: #f8d7da; border-color: #f5c6cb; }
        .summary { background: #e2e3e5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f2f2f2; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Jive Consolidated Tools - Comprehensive Test Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Total Duration:</strong> {duration:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="metric">
            <strong>Total Phases:</strong> {total_phases}
        </div>
        <div class="metric">
            <strong>Passed:</strong> {passed_phases}
        </div>
        <div class="metric">
            <strong>Failed:</strong> {failed_phases}
        </div>
        <div class="metric">
            <strong>Success Rate:</strong> {success_rate:.1f}%
        </div>
    </div>
    
    <h2>Legacy Capability Validation</h2>
    <table>
        <tr>
            <th>Unified Tool</th>
            <th>Legacy Tools Replaced</th>
            <th>Count</th>
            <th>Status</th>
        </tr>
        {legacy_table_rows}
    </table>
    
    <h2>Phase Results</h2>
    {phase_results}
    
    <div class="summary">
        <h2>Conclusion</h2>
        <p>This comprehensive test validates that all 32 legacy tool capabilities are preserved in the 7 consolidated tools.</p>
        <p><strong>Overall Status:</strong> {overall_status}</p>
    </div>
</body>
</html>
        """
        
        # Calculate metrics
        summary = self.results["summary"]
        success_rate = (summary["passed_phases"] / summary["total_phases"]) * 100 if summary["total_phases"] > 0 else 0
        overall_status = "PASSED" if summary["failed_phases"] == 0 else "FAILED"
        
        # Generate legacy capability table
        legacy_rows = []
        for tool, legacy_tools in LEGACY_TOOL_MAPPING.items():
            legacy_list = ", ".join(legacy_tools)
            status = "✅ Validated" if summary["failed_phases"] == 0 else "❌ Needs Review"
            legacy_rows.append(f"""
                <tr>
                    <td>{tool}</td>
                    <td>{legacy_list}</td>
                    <td>{len(legacy_tools)}</td>
                    <td>{status}</td>
                </tr>
            """)
        
        # Generate phase results
        phase_html = []
        for phase_name, phase_result in self.results["phases"].items():
            css_class = "success" if phase_result["success"] else "failure"
            status_icon = "✅" if phase_result["success"] else "❌"
            
            phase_html.append(f"""
                <div class="phase {css_class}">
                    <h3>{status_icon} {phase_result['name']}</h3>
                    <p><strong>Duration:</strong> {phase_result.get('duration', 0):.2f}s</p>
                    <p><strong>Tests Run:</strong> {phase_result.get('tests_run', 'N/A')}</p>
                    <p><strong>Tests Passed:</strong> {phase_result.get('tests_passed', 'N/A')}</p>
                    <p><strong>Tests Failed:</strong> {phase_result.get('tests_failed', 'N/A')}</p>
                </div>
            """)
        
        return html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=summary["total_duration"],
            total_phases=summary["total_phases"],
            passed_phases=summary["passed_phases"],
            failed_phases=summary["failed_phases"],
            success_rate=success_rate,
            legacy_table_rows="".join(legacy_rows),
            phase_results="".join(phase_html),
            overall_status=overall_status
        )
    
    def save_reports(self):
        """Save test reports to files."""
        if not self.results:
            self.log("No results to save", "WARNING")
            return
        
        # Save JSON report
        if self.json_report:
            json_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            self.log(f"JSON report saved: {json_file}", "SUCCESS")
        
        # Save HTML report
        if self.generate_report:
            html_content = self.generate_html_report()
            html_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_file, 'w') as f:
                f.write(html_content)
            self.log(f"HTML report saved: {html_file}", "SUCCESS")
    
    def print_summary(self):
        """Print test execution summary."""
        if not self.results:
            self.log("No results available", "WARNING")
            return
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST EXECUTION SUMMARY")
        print("="*80)
        
        summary = self.results["summary"]
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"Phases Run: {summary['total_phases']}")
        print(f"Phases Passed: {summary['passed_phases']}")
        print(f"Phases Failed: {summary['failed_phases']}")
        
        success_rate = (summary['passed_phases'] / summary['total_phases']) * 100 if summary['total_phases'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nLegacy Capability Validation:")
        total_legacy = sum(len(tools) for tools in LEGACY_TOOL_MAPPING.values())
        print(f"  • Total Legacy Tools: {total_legacy}")
        print(f"  • Unified Tools: {len(LEGACY_TOOL_MAPPING)}")
        print(f"  • Consolidation Ratio: {((total_legacy - len(LEGACY_TOOL_MAPPING)) / total_legacy * 100):.1f}% reduction")
        
        print("\nPhase Details:")
        for phase_name, phase_result in self.results["phases"].items():
            status = "✅ PASSED" if phase_result["success"] else "❌ FAILED"
            duration = phase_result.get("duration", 0)
            tests_run = phase_result.get("tests_run", "N/A")
            print(f"  • {phase_result['name']}: {status} ({duration:.2f}s, {tests_run} tests)")
        
        overall_status = "✅ ALL TESTS PASSED" if summary['failed_phases'] == 0 else "❌ SOME TESTS FAILED"
        print(f"\nOverall Status: {overall_status}")
        print("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for consolidated MCP Jive tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_comprehensive_tests.py unit --verbose
  python run_comprehensive_tests.py all --report --json
  python run_comprehensive_tests.py performance --coverage
        """
    )
    
    parser.add_argument(
        "phase",
        choices=["unit", "integration", "performance", "all"],
        help="Test phase to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Generate HTML report"
    )
    
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Generate JSON report"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Include code coverage"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(
        verbose=args.verbose,
        generate_report=args.report,
        json_report=args.json,
        coverage=args.coverage
    )
    
    try:
        # Run tests
        if args.phase == "all":
            results = runner.run_all_phases()
        else:
            result = runner.run_phase(args.phase)
            results = {
                "phases": {args.phase: result},
                "summary": {
                    "total_phases": 1,
                    "passed_phases": 1 if result["success"] else 0,
                    "failed_phases": 0 if result["success"] else 1,
                    "total_duration": result.get("duration", 0)
                }
            }
            runner.results = results
        
        # Generate reports
        runner.save_reports()
        
        # Print summary
        runner.print_summary()
        
        # Exit with appropriate code
        if results["summary"]["failed_phases"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        runner.log("Test execution interrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        runner.log(f"Test execution failed: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()