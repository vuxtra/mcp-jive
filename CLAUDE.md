# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Jive is an autonomous AI code builder that implements the Model Context Protocol (MCP). It provides intelligent project management capabilities for AI agents through 8 consolidated tools, using LanceDB as an embedded vector database for semantic search and data persistence.

## Commands

### Development Commands

**Start development server:**
```bash
./bin/mcp-jive dev server
```

**Start production server:**
```bash
# Combined mode (HTTP + WebSocket, default)
./bin/mcp-jive server start --mode combined --port 3454

# Stdio mode (for MCP client integration)
./bin/mcp-jive server start --mode stdio

# HTTP mode only
./bin/mcp-jive server start --mode http --port 3454
```

**Database Management:**
```bash
# Reset development database
./bin/mcp-jive dev reset-db

# Check database status
./bin/mcp-jive dev check-db
```

**Testing:**
```bash
# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/           # Unit tests
python -m pytest tests/integration/   # Integration tests
./bin/mcp-jive test e2e               # End-to-end tests

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

**Installation & Setup:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Setup environment
./bin/mcp-jive setup install
```

### Health Checks

```bash
# Check server health (when running)
curl http://localhost:3454/health

# Development server health
curl http://localhost:3456/health
```

## Architecture

### Core Components

**Server Architecture:**
- `src/mcp_jive/server.py` - Main MCP server implementation
- `src/mcp_jive/config.py` - Configuration management
- `src/mcp_jive/lancedb_manager.py` - Database connection and management

**Tool System:**
- `src/mcp_jive/tools/consolidated/` - 7 consolidated MCP tools
  - `unified_work_item_tool.py` - CRUD operations for work items
  - `unified_retrieval_tool.py` - Advanced filtering and listing
  - `unified_search_tool.py` - Semantic, keyword, and hybrid search
  - `unified_hierarchy_tool.py` - Hierarchy and dependency navigation
  - `unified_execution_tool.py` - Work item and workflow execution
  - `unified_progress_tool.py` - Progress tracking and analytics
  - `unified_storage_tool.py` - Data storage and synchronization

**Services:**
- `src/mcp_jive/services/hierarchy_manager.py` - Work item hierarchy management
- `src/mcp_jive/services/dependency_engine.py` - Dependency validation and resolution
- `src/mcp_jive/services/sync_engine.py` - Data synchronization
- `src/mcp_jive/services/progress_calculator.py` - Progress calculation logic

**Data Models:**
- Work items follow hierarchical structure: Initiative → Epic → Feature → Story → Task
- All data persisted in LanceDB with namespace support for multi-tenancy
- Vector embeddings for semantic search using sentence-transformers

### Key Architecture Patterns

1. **Consolidated Tools**: 8 unified tools replace legacy tool system for simplified AI agent interaction
2. **LanceDB Integration**: Embedded vector database with no external dependencies
3. **Namespace Isolation**: Multi-tenant data separation with namespace-aware operations
4. **MCP Protocol**: Full compliance with Model Context Protocol for IDE integration
5. **Transport Modes**: Supports stdio (MCP clients), HTTP (APIs), and combined modes

### Database Schema

The system uses LanceDB tables:
- `WorkItem` - All work item types with hierarchical relationships
- `Task` - Legacy table, migrated to WorkItem
- `SearchIndex` - Vector embeddings for semantic search
- `ExecutionLog` - Workflow execution history
- `WorkItemDependency` - Dependency relationships

### Configuration

Configuration is managed through:
- `.env` file (copy from `.env.example`)
- Environment variables with `MCP_JIVE_` prefix
- Command-line arguments via `./bin/mcp-jive`

Key settings:
- `LANCEDB_DATA_PATH` - Database storage location (default: `./data/lancedb_jive`)
- `MCP_JIVE_PORT` - Server port (default: 3454)
- `MCP_JIVE_DEBUG` - Enable debug logging

### Development Patterns

When working with this codebase:

1. **Tool Development**: Use consolidated tools in `src/mcp_jive/tools/consolidated/` - avoid legacy tools
2. **Database Operations**: Always use `LanceDBManager` for database interactions
3. **Error Handling**: Use structured error responses with success/error status
4. **Async Operations**: Most operations are async - use `await` appropriately
5. **Namespace Awareness**: Ensure all operations respect namespace context
6. **Testing**: Write tests in appropriate directories (`tests/unit/`, `tests/integration/`)
7. **Browser Testing**: Use chrome-devtools MCP tools for frontend testing and debugging
8. **Documentation**: Always refer to and update project documentation in `docs/` folder

### Documentation Guidelines

**IMPORTANT**: Always refer to existing documentation before making changes and update relevant docs when making architectural changes.

1. **Documentation Structure**:
   - `docs/` - Root documentation folder
   - `docs/architecture/` - Architecture documentation and decisions
   - `docs/architecture/decisions/` - Architecture Decision Records (ADRs)

2. **Key Documentation Files**:
   - `docs/CONSOLIDATED_TOOLS_IMPLEMENTATION_GUIDE.md` - Implementation guide for MCP tools
   - `docs/CONSOLIDATED_TOOLS_USAGE_GUIDE.md` - Usage guide for MCP tools
   - `docs/comprehensive_mcp_tools_reference.md` - Complete tools reference
   - `docs/architecture/namespace-architecture.md` - Namespace system architecture
   - `docs/mcp-namespace-binding.md` - MCP namespace binding documentation
   - `docs/namespace-feature-usage.md` - Namespace feature usage patterns
   - `docs/URL_NAMESPACE_IMPLEMENTATION.md` - URL namespace implementation
   - `docs/architecture/decisions/adr-001-react-framework-selection.md` - React framework ADR

3. **Documentation Workflow**:
   - **Before Changes**: Always read relevant docs to understand current architecture
   - **During Development**: Follow patterns and guidelines from existing documentation
   - **After Changes**: Update documentation if architecture, APIs, or patterns change
   - **New Features**: Document new features, tools, or architectural decisions

4. **When to Update Documentation**:
   - Adding new MCP tools or modifying existing ones
   - Changing namespace behavior or architecture
   - Modifying API interfaces or data models
   - Adding new configuration options
   - Making architectural decisions (create new ADRs)
   - Changing development workflows or patterns

5. **Documentation Standards**:
   - Use clear, concise language
   - Include code examples where relevant
   - Keep documentation up-to-date with code changes
   - Follow existing documentation structure and style

### Browser Testing & Debugging

When testing browser functionality, rendering, or debugging frontend issues:

1. **Use Chrome DevTools MCP Tools**: The `mcp__chrome-devtools__*` tools are available for browser interaction
2. **Common Browser Testing Tasks**:
   - `mcp__chrome-devtools__take_snapshot` - Get DOM structure and element UIDs
   - `mcp__chrome-devtools__list_console_messages` - Access browser console logs and errors
   - `mcp__chrome-devtools__list_network_requests` - Monitor network activity
   - `mcp__chrome-devtools__navigate_page` - Navigate to test URLs
   - `mcp__chrome-devtools__take_screenshot` - Visual verification of rendering
   - `mcp__chrome-devtools__click`, `mcp__chrome-devtools__fill` - User interaction testing

3. **Testing Workflow**:
   - Start the development server: `./bin/mcp-jive dev server` (port 3453)
   - Navigate browser to `http://localhost:3453/`
   - Use DevTools MCP tools to inspect, interact, and debug
   - Check console for errors and network requests for API issues

4. **Frontend URLs**:
   - Development UI: `http://localhost:3453/`

## Development Workflow

### Research-First Approach

**ALWAYS research before implementing:**

1. **Check Official Documentation**: Start with official docs of any libraries, frameworks, or tools involved
2. **Review Existing Documentation**: Check our `docs/` folder for existing patterns and architectural decisions
3. **Research Multiple Solutions**: Investigate at least 2-3 different approaches before selecting one
4. **Compare Trade-offs**: Evaluate pros/cons, performance, maintainability, and alignment with project goals
5. **Confirm Major Changes**: Always seek user confirmation before implementing significant architectural changes

### Task Management with MCP Jive

**Use MCP Jive tools for all significant work:**

1. **Large Initiatives**: Create Initiative-level work items for major features or refactors
2. **Epic Breakdown**: Break initiatives into Epics for logical feature groupings
3. **Feature Planning**: Create Features under Epics for specific functionality
4. **Task Tracking**: Create Stories and Tasks for individual implementation units
5. **Progress Updates**: Use MCP Jive tools to track progress throughout implementation

**Example Workflow:**
```bash
# Research phase
# 1. Check official docs for technology X
# 2. Review docs/architecture/ for existing patterns
# 3. Research 2-3 implementation approaches
# 4. Compare solutions and document decision

# Planning phase - Use MCP Jive tools
mcp_jive_manage_work_item(action="create", type="initiative", title="Implement Feature X")
mcp_jive_manage_work_item(action="create", type="epic", title="Backend API", parent_id="...")
mcp_jive_manage_work_item(action="create", type="feature", title="Authentication", parent_id="...")

# Implementation phase - Update progress
mcp_jive_track_progress(action="track", work_item_id="...", progress_data={...})
```

### Implementation Standards

1. **Breakdown Complex Work**:
   - Large initiatives → Epics → Features → Stories → Tasks
   - Each task should be completable in 1-4 hours
   - Clear acceptance criteria for each work item

2. **Research Documentation**:
   - Always check existing ADRs in `docs/architecture/decisions/`
   - Follow established patterns in consolidated tools
   - Document new architectural decisions

3. **Validation Process**:
   - Confirm scope and approach with user before major changes
   - Use MCP Jive execution planning for complex workflows
   - Test locally before implementing

4. **Progress Tracking**:
   - Update work item status as you progress
   - Use progress percentages and notes
   - Track blockers and dependencies

### Development Best Practices

**Before Starting Work:**
- ✅ Research official documentation
- ✅ Check existing project documentation
- ✅ Research multiple implementation approaches
- ✅ Create MCP Jive work items for tracking
- ✅ Confirm approach with user (for major changes)

**During Implementation:**
- ✅ Follow established architectural patterns
- ✅ Update progress in MCP Jive tools regularly
- ✅ Document decisions and trade-offs
- ✅ Test components as you build

**After Implementation:**
- ✅ Update documentation if patterns changed
- ✅ Mark work items as completed
- ✅ Run tests and validate functionality
- ✅ Create ADRs for significant decisions

### Temporary Files Management

#### Temporary Scripts

**IMPORTANT**: All temporary, testing, and one-time use scripts should be created in the `/scripts/temp/` directory.

**Guidelines for Temporary Scripts:**
1. **Location**: Always create temporary scripts in `/scripts/temp/` directory
2. **Naming**: Use descriptive prefixes:
   - `debug_*.py` - Debugging and diagnostic scripts
   - `check_*.py` - Validation and verification scripts
   - `fix_*.py` - Problem resolution scripts
   - `test_*.py` - Testing and experimentation
   - `migrate_*.py` - Data migration utilities
   - `demo_*.py` - Demonstration scripts
   - `run_*.py` - Execution helpers
3. **Documentation**: Include brief comments explaining the script's purpose
4. **Cleanup**: Remove scripts when no longer needed
5. **Git Ignore**: The entire `/scripts/temp/` directory is excluded from version control

**Example:**
```bash
# ❌ Don't create in root
./debug_new_feature.py

# ✅ Create in temp directory
./scripts/temp/debug_new_feature.py
```

#### Temporary Documentation

**IMPORTANT**: All temporary, draft, and experimental documentation should be created in the `/docs/temp/` directory.

**Guidelines for Temporary Documentation:**
1. **Location**: Always create temporary docs in `/docs/temp/` directory
2. **Naming**: Use descriptive patterns:
   - `*_ANALYSIS.md` - Analysis and investigation documents
   - `*_IMPLEMENTATION*.md` - Implementation guides and notes
   - `*_TEST*.md` - Test reports and analysis
   - `*_prompts.md` - AI prompt files and conversation logs
   - `*_GUIDE.md` - Temporary guides and how-to documents
   - `*_REPORT.md` - Status reports and summaries
   - `*_DEBUG*.md` - Debugging and troubleshooting docs
3. **Core Docs in Root**: Only essential docs stay in project root:
   - `README.md` - Main project documentation
   - `CONTRIBUTING.md` - Contribution guidelines
   - `CLAUDE.md` - This development guide
   - `RELEASES.md` - Release information
   - `CHANGELOG.md` - Version history (when created)
4. **Cleanup**: Move finalized content to proper documentation locations
5. **Git Ignore**: The entire `/docs/temp/` directory is excluded from version control

**Why This Structure:**
- Keeps project root clean and organized
- Prevents accidental exclusion of legitimate documentation via pattern matching
- Provides dedicated space for experimental and draft documentation
- Maintains clear separation between production and temporary documentation
- Follows same pattern as scripts organization

**Example:**
```bash
# ❌ Don't create in root
./NEW_FEATURE_ANALYSIS.md
./debug_prompts.md

# ✅ Create in temp directory
./docs/temp/NEW_FEATURE_ANALYSIS.md
./docs/temp/debug_prompts.md
```

### Entry Points

- `./bin/mcp-jive` - Main CLI interface
- `mcp-server.py` - Direct server startup (fallback)
- `setup.py` - Python package installation

The unified CLI (`./bin/mcp-jive`) is the preferred way to interact with the system and provides comprehensive command routing.