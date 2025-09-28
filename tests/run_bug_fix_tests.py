#!/usr/bin/env python3
"""Test runner for MCP Jive bug fix validation.

This script runs all bug fix tests in the correct order:
1. Unit tests for individual components
2. Integration tests for component interactions
3. Validation tests for end-to-end verification

Usage:
    python run_bug_fix_tests.py [--verbose] [--test-type TYPE] [--output-dir DIR]
"""

import asyncio
import subprocess
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestResult:
    """Result of a test execution."""
    test_type: str
    test_file: str
    passed: bool
    duration: float
    output: str
    error: Optional[str] = None


class BugFixTestRunner:
    """Comprehensive test runner for bug fix validation."""
    
    def __init__(self, verbose: bool = False, output_dir: Optional[Path] = None):
        self.verbose = verbose
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[TestResult] = []
        
        # Test configuration
        self.test_files = {
            "unit": [
                "tests/unit/test_ai_guidance_generator_fixes.py",
                "tests/unit/test_status_monitoring_fixes.py",
                "tests/unit/test_hierarchy_validation_fixes.py"
            ],
            "integration": [
                "tests/integration/test_bug_fixes_integration.py"
            ],
            "validation": [
                "tests/validation/test_bug_fixes_validation.py"
            ]
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    async def run_pytest_tests(self, test_type: str, test_files: List[str]) -> List[TestResult]:
        """Run pytest tests for given files."""
        results = []
        
        for test_file in test_files:
            self.log(f"Running {test_type} test: {test_file}")
            
            start_time = time.time()
            
            # Build pytest command
            cmd = [
                sys.executable, "-m", "pytest", 
                test_file,
                "-v" if self.verbose else "-q",
                "--tb=short",
                f"--junitxml={self.output_dir}/{test_type}_{Path(test_file).stem}.xml"
            ]
            
            try:
                # Run pytest
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=Path.cwd()
                )
                
                stdout, stderr = await process.communicate()
                duration = time.time() - start_time
                
                # Determine if tests passed
                passed = process.returncode == 0
                
                output = stdout.decode('utf-8') if stdout else ""
                error = stderr.decode('utf-8') if stderr else None
                
                result = TestResult(
                    test_type=test_type,
                    test_file=test_file,
                    passed=passed,
                    duration=duration,
                    output=output,
                    error=error
                )
                
                results.append(result)
                
                status = "PASSED" if passed else "FAILED"
                self.log(f"{test_file} {status} in {duration:.2f}s")
                
                if not passed and self.verbose:
                    self.log(f"Error output: {error}", "ERROR")
                
            except Exception as e:
                duration = time.time() - start_time
                result = TestResult(
                    test_type=test_type,
                    test_file=test_file,
                    passed=False,
                    duration=duration,
                    output="",
                    error=f"Failed to run test: {str(e)}"
                )
                results.append(result)
                self.log(f"Failed to run {test_file}: {str(e)}", "ERROR")
        
        return results
    
    async def run_validation_script(self) -> TestResult:
        """Run the comprehensive validation script."""
        self.log("Running comprehensive validation script")
        
        start_time = time.time()
        
        cmd = [
            sys.executable,
            "tests/validation/test_bug_fixes_validation.py",
            "--output", str(self.output_dir / "validation_report.json")
        ]
        
        if self.verbose:
            cmd.append("--verbose")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            stdout, stderr = await process.communicate()
            duration = time.time() - start_time
            
            passed = process.returncode == 0
            output = stdout.decode('utf-8') if stdout else ""
            error = stderr.decode('utf-8') if stderr else None
            
            result = TestResult(
                test_type="validation",
                test_file="tests/validation/test_bug_fixes_validation.py",
                passed=passed,
                duration=duration,
                output=output,
                error=error
            )
            
            status = "PASSED" if passed else "FAILED"
            self.log(f"Validation script {status} in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                test_type="validation",
                test_file="tests/validation/test_bug_fixes_validation.py",
                passed=False,
                duration=duration,
                output="",
                error=f"Failed to run validation script: {str(e)}"
            )
            self.log(f"Failed to run validation script: {str(e)}", "ERROR")
            return result
    
    async def run_all_tests(self, test_type: Optional[str] = None) -> List[TestResult]:
        """Run all tests or specific test type."""
        self.log("Starting comprehensive bug fix test execution...")
        
        all_results = []
        
        # Determine which test types to run
        test_types = [test_type] if test_type else ["unit", "integration", "validation"]
        
        for current_test_type in test_types:
            if current_test_type == "validation":
                # Run validation script
                result = await self.run_validation_script()
                all_results.append(result)
            else:
                # Run pytest tests
                if current_test_type in self.test_files:
                    test_files = self.test_files[current_test_type]
                    results = await self.run_pytest_tests(current_test_type, test_files)
                    all_results.extend(results)
                else:
                    self.log(f"Unknown test type: {current_test_type}", "WARNING")
        
        self.results = all_results
        return all_results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(r.duration for r in self.results)
        
        # Group results by test type
        by_type = {}
        for result in self.results:
            test_type = result.test_type
            if test_type not in by_type:
                by_type[test_type] = {"passed": 0, "failed": 0, "duration": 0.0, "tests": []}
            
            by_type[test_type]["tests"].append({
                "file": result.test_file,
                "passed": result.passed,
                "duration": result.duration,
                "error": result.error
            })
            
            if result.passed:
                by_type[test_type]["passed"] += 1
            else:
                by_type[test_type]["failed"] += 1
            
            by_type[test_type]["duration"] += result.duration
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_duration": total_duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "by_type": by_type,
            "results": [
                {
                    "test_type": r.test_type,
                    "test_file": r.test_file,
                    "passed": r.passed,
                    "duration": r.duration,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        return report
    
    def print_report(self) -> bool:
        """Print human-readable test report."""
        report = self.generate_report()
        
        print("\n" + "=" * 70)
        print("MCP JIVE BUG FIX TESTS REPORT")
        print("=" * 70)
        
        summary = report["summary"]
        print(f"\nOVERALL SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Total Duration: {summary['total_duration']:.2f}s")
        print(f"  Timestamp: {summary['timestamp']}")
        
        print(f"\nBY TEST TYPE:")
        for test_type, data in report["by_type"].items():
            total = data["passed"] + data["failed"]
            success_rate = (data["passed"] / total * 100) if total > 0 else 0
            print(f"  {test_type.upper()}:")
            print(f"    Tests: {total} | Passed: {data['passed']} | Failed: {data['failed']}")
            print(f"    Success Rate: {success_rate:.1f}% | Duration: {data['duration']:.2f}s")
        
        print(f"\nDETAILED RESULTS:")
        for test_type, data in report["by_type"].items():
            print(f"\n{test_type.upper()} TESTS:")
            for test in data["tests"]:
                status = "✅ PASSED" if test["passed"] else "❌ FAILED"
                file_name = Path(test["file"]).name
                print(f"  {status} {file_name} ({test['duration']:.2f}s)")
                
                if test["error"] and self.verbose:
                    print(f"    Error: {test['error']}")
        
        print("\n" + "=" * 70)
        
        if summary["failed"] > 0:
            print(f"❌ TESTS FAILED: {summary['failed']} test(s) failed")
            return False
        else:
            print("✅ ALL TESTS PASSED")
            return True
    
    def save_report(self, filename: str = "test_report.json"):
        """Save test report to file."""
        report = self.generate_report()
        report_path = self.output_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"Test report saved to: {report_path}")


async def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run MCP Jive bug fix tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--test-type", 
        choices=["unit", "integration", "validation"],
        help="Run only specific test type"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=Path("test_results"),
        help="Output directory for test results"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating test report"
    )
    
    args = parser.parse_args()
    
    runner = BugFixTestRunner(
        verbose=args.verbose,
        output_dir=args.output_dir
    )
    
    print("Starting MCP Jive bug fix test execution...")
    
    try:
        # Run tests
        results = await runner.run_all_tests(test_type=args.test_type)
        
        # Generate and print report
        if not args.no_report:
            success = runner.print_report()
            runner.save_report()
        else:
            success = all(r.passed for r in results)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed with unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())