#!/bin/bash
# E2E Test Runner Script for MCP Jive
# This script provides an easy way to run E2E tests with various options

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
OUTPUT_DIR="$PROJECT_ROOT/test_results"
VERBOSE=false
PERFORMANCE=true
CLEAN=false
HELP=false

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
E2E Test Runner for MCP Jive

Usage: $0 [OPTIONS]

Options:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -o, --output-dir DIR    Set output directory (default: test_results)
    --no-performance        Skip performance tests
    --clean                 Clean output directory before running
    --quick                 Run only essential tests (no performance)
    --ci                    CI mode (clean + no performance + verbose)

Examples:
    $0                      # Run all tests with default settings
    $0 --verbose            # Run with verbose output
    $0 --quick              # Quick test run without performance tests
    $0 --ci                 # CI/CD pipeline mode
    $0 --clean -o results   # Clean results directory and run tests

Environment Variables:
    E2E_OUTPUT_DIR          Override default output directory
    E2E_VERBOSE             Set to 'true' to enable verbose mode
    E2E_NO_PERFORMANCE      Set to 'true' to skip performance tests

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            HELP=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --no-performance)
            PERFORMANCE=false
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --quick)
            PERFORMANCE=false
            shift
            ;;
        --ci)
            CLEAN=true
            PERFORMANCE=false
            VERBOSE=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Show help if requested
if [[ "$HELP" == "true" ]]; then
    show_help
    exit 0
fi

# Override with environment variables if set
if [[ -n "$E2E_OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$E2E_OUTPUT_DIR"
fi

if [[ "$E2E_VERBOSE" == "true" ]]; then
    VERBOSE=true
fi

if [[ "$E2E_NO_PERFORMANCE" == "true" ]]; then
    PERFORMANCE=false
fi

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Print configuration
print_info "E2E Test Configuration:"
echo "  Project Root: $PROJECT_ROOT"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Verbose Mode: $VERBOSE"
echo "  Performance Tests: $PERFORMANCE"
echo "  Clean Output: $CLEAN"
echo ""

# Clean output directory if requested
if [[ "$CLEAN" == "true" ]]; then
    print_info "Cleaning output directory: $OUTPUT_DIR"
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "No virtual environment detected. Make sure dependencies are installed."
fi

# Check if required dependencies are available
print_info "Checking dependencies..."
if ! python -c "import pytest" 2>/dev/null; then
    print_error "pytest not found. Please install test dependencies: pip install -e .[test]"
    exit 1
fi

if ! python -c "import pytest_asyncio" 2>/dev/null; then
    print_error "pytest-asyncio not found. Please install test dependencies: pip install -e .[test]"
    exit 1
fi

print_success "Dependencies check passed"

# Build command arguments
CMD_ARGS=()
CMD_ARGS+=("--output-dir" "$OUTPUT_DIR")

if [[ "$VERBOSE" == "true" ]]; then
    CMD_ARGS+=("--verbose")
fi

if [[ "$PERFORMANCE" == "false" ]]; then
    CMD_ARGS+=("--no-performance")
fi

# Run the E2E tests
print_info "Starting E2E test execution..."
echo "Command: python scripts/run_e2e_tests.py ${CMD_ARGS[*]}"
echo ""

# Execute the test runner
if python "scripts/run_e2e_tests.py" "${CMD_ARGS[@]}"; then
    print_success "E2E tests completed successfully!"
    
    # Show quick summary of results
    if [[ -f "$OUTPUT_DIR/e2e_test_report.md" ]]; then
        print_info "Quick Summary:"
        grep -E "^- \*\*" "$OUTPUT_DIR/e2e_test_report.md" | head -6 || true
    fi
    
    print_info "Detailed reports available in: $OUTPUT_DIR"
    echo "  - Human-readable: $OUTPUT_DIR/e2e_test_report.md"
    echo "  - JSON report: $OUTPUT_DIR/comprehensive_e2e_report.json"
    
    if [[ -f "$OUTPUT_DIR/pytest_e2e_report.html" ]]; then
        echo "  - Pytest HTML: $OUTPUT_DIR/pytest_e2e_report.html"
    fi
    
    exit 0
else
    print_error "E2E tests failed!"
    
    if [[ -f "$OUTPUT_DIR/e2e_test_report.md" ]]; then
        print_info "Error summary:"
        grep -A 10 "## Errors" "$OUTPUT_DIR/e2e_test_report.md" || true
    fi
    
    print_info "Check detailed reports in: $OUTPUT_DIR"
    exit 1
fi