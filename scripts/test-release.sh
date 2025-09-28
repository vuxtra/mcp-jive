#!/bin/bash

# 🧪 Test Release System
# This script simulates the release process locally for testing

set -e

echo "🧪 Testing MCP Jive Release System"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "\n${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "setup.py" ]]; then
    print_error "setup.py not found. Please run this script from the project root."
    exit 1
fi

print_step "Checking current version"
CURRENT_VERSION=$(grep -o 'version="[^"]*"' setup.py | sed 's/version="\(.*\)"/\1/')
echo "Current version: $CURRENT_VERSION"
print_success "Version found in setup.py"

print_step "Validating conventional commits"
# Get recent commits
COMMITS=$(git log --oneline -10 --pretty=format:"%s")
VALID_TYPES=("feat" "fix" "docs" "style" "refactor" "perf" "test" "chore" "ci" "build")
CONVENTIONAL_COUNT=0
TOTAL_COMMITS=0

while IFS= read -r commit; do
    if [[ -n "$commit" ]]; then
        TOTAL_COMMITS=$((TOTAL_COMMITS + 1))

        # Check if commit follows conventional format
        for type in "${VALID_TYPES[@]}"; do
            if [[ $commit =~ ^$type(\(.+\))?:\ .+ ]]; then
                CONVENTIONAL_COUNT=$((CONVENTIONAL_COUNT + 1))
                echo "  ✅ $commit"
                break
            fi
        done

        # Check for breaking changes
        if [[ $commit =~ BREAKING\ CHANGE ]] || [[ $commit =~ !: ]]; then
            echo "  💥 BREAKING: $commit"
        fi
    fi
done <<< "$COMMITS"

if [[ $CONVENTIONAL_COUNT -gt 0 ]]; then
    print_success "$CONVENTIONAL_COUNT/$TOTAL_COMMITS commits follow conventional format"
else
    print_warning "No conventional commits found in recent history"
fi

print_step "Analyzing release type"
# Simulate release type detection
if echo "$COMMITS" | grep -q "BREAKING CHANGE\|!:"; then
    RELEASE_TYPE="major"
    print_warning "BREAKING CHANGE detected → Major release"
elif echo "$COMMITS" | grep -q "^feat"; then
    RELEASE_TYPE="minor"
    echo "New features detected → Minor release"
elif echo "$COMMITS" | grep -q "^fix"; then
    RELEASE_TYPE="patch"
    echo "Bug fixes detected → Patch release"
else
    RELEASE_TYPE="none"
    echo "No significant changes → No release"
fi

print_step "Calculating new version"
IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

case "$RELEASE_TYPE" in
    "major")
        NEW_VERSION="$((MAJOR + 1)).0.0"
        ;;
    "minor")
        NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
        ;;
    "patch")
        NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
        ;;
    *)
        NEW_VERSION="$CURRENT_VERSION"
        ;;
esac

echo "New version would be: $NEW_VERSION"
if [[ "$NEW_VERSION" != "$CURRENT_VERSION" ]]; then
    print_success "Version bump: $CURRENT_VERSION → $NEW_VERSION"
else
    print_warning "No version change needed"
fi

print_step "Testing package build"
if command -v python &> /dev/null; then
    # Test setup.py
    python setup.py check
    print_success "setup.py is valid"

    # Test if package can be built
    if command -v build &> /dev/null; then
        echo "Testing package build..."
        python -m build --wheel --outdir /tmp/test-build
        print_success "Package builds successfully"
        rm -rf /tmp/test-build
    else
        print_warning "build module not installed, skipping build test"
    fi
else
    print_error "Python not found"
    exit 1
fi

print_step "Checking GitHub Actions workflows"
WORKFLOWS_DIR=".github/workflows"
if [[ -d "$WORKFLOWS_DIR" ]]; then
    echo "Found workflows:"
    for workflow in "$WORKFLOWS_DIR"/*.yml; do
        if [[ -f "$workflow" ]]; then
            WORKFLOW_NAME=$(basename "$workflow")
            echo "  📄 $WORKFLOW_NAME"
        fi
    done
    print_success "GitHub Actions workflows are present"
else
    print_error "No GitHub Actions workflows found"
    exit 1
fi

print_step "Validating workflow syntax"
if command -v yamllint &> /dev/null; then
    for workflow in "$WORKFLOWS_DIR"/*.yml; do
        if yamllint "$workflow" >/dev/null 2>&1; then
            echo "  ✅ $(basename "$workflow") - Valid YAML"
        else
            echo "  ❌ $(basename "$workflow") - Invalid YAML"
        fi
    done
else
    print_warning "yamllint not installed, skipping YAML validation"
fi

print_step "Testing Git operations"
# Check if we can create tags (dry run)
if git tag --dry-run "v$NEW_VERSION" 2>/dev/null; then
    print_success "Git tag creation would succeed"
else
    print_warning "Git tag v$NEW_VERSION already exists or would fail"
fi

# Check repository status
if [[ -n $(git status --porcelain) ]]; then
    print_warning "Repository has uncommitted changes"
    git status --short
else
    print_success "Repository is clean"
fi

print_step "Summary"
echo "=============================="
echo "Current Version: $CURRENT_VERSION"
echo "Release Type: $RELEASE_TYPE"
echo "New Version: $NEW_VERSION"
echo "Conventional Commits: $CONVENTIONAL_COUNT/$TOTAL_COMMITS"
echo ""

if [[ "$RELEASE_TYPE" != "none" ]]; then
    print_success "✅ Release system is ready!"
    echo ""
    echo "Next steps to create a release:"
    echo "1. Ensure all changes are committed"
    echo "2. Push to main branch (triggers automatic release)"
    echo "3. Or use manual workflow in GitHub Actions"
else
    print_warning "⚠️  No release would be triggered"
    echo ""
    echo "To trigger a release:"
    echo "1. Make commits with feat:/fix: prefixes"
    echo "2. Or use manual version bump workflow"
fi

echo ""
echo "🔗 Useful links:"
echo "   📖 Release Process: docs/RELEASE_PROCESS.md"
echo "   🤖 GitHub Actions: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions"
echo "   🏷️  Releases: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/releases"