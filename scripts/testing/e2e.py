#!/usr/bin/env python3
"""
End-to-End Test Runner

Wrapper for running e2e tests with enhanced functionality.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run end-to-end tests")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--filter", "-f", type=str, 
                       help="Filter tests by pattern")
    parser.add_argument("--timeout", "-t", type=int, default=300,
                       help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    e2e_script = script_dir / "e2e-test.sh"
    
    if not e2e_script.exists():
        print(f"Error: e2e test script not found at {e2e_script}")
        return 1
    
    # Prepare command
    cmd = ["bash", str(e2e_script)]
    
    # Set environment variables based on arguments
    env = os.environ.copy()
    if args.verbose:
        env["E2E_VERBOSE"] = "1"
    if args.filter:
        env["E2E_FILTER"] = args.filter
    if args.timeout:
        env["E2E_TIMEOUT"] = str(args.timeout)
    
    try:
        print("Starting end-to-end tests...")
        result = subprocess.run(cmd, env=env, timeout=args.timeout)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"Error: Tests timed out after {args.timeout} seconds")
        return 124
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())