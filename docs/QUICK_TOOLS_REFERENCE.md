# Quick MCP Jive Tools Reference

**Last Updated**: 2025-01-03 | **Total Tools**: 35 (Full Mode) / 16 (Minimal Mode)

## Tool Categories Overview

| Category | Tools Count | Minimal Mode | Full Mode | Purpose |
|----------|-------------|--------------|-----------|----------|
| **Core Work Item Management** | 5 | ✅ | ✅ | CRUD operations for work items |
| **Hierarchy Management** | 6 | ⚠️ (3) | ✅ | Work item relationships and dependencies |
| **Storage Sync** | 3 | ✅ | ✅ | File-database synchronization |
| **Validation** | 5 | ⚠️ (2) | ✅ | Quality gates and approval workflows |
| **AI Orchestration** | 3 | ✅ | ✅ | Multi-provider AI coordination |
| **Search & Discovery** | 4 | ❌ | ✅ | Content search and discovery |
| **Task Management** | 4 | ❌ | ✅ | Development task operations |
| **Progress Tracking** | 4 | ❌ | ✅ | Progress monitoring and analytics |
| **Workflow Execution** | 4 | ❌ | ✅ | Workflow orchestration |

## Quick Tool Lookup

### Core Work Item Management (Always Available)
```bash
jive_create_work_item      # Create new work items (Initiative→Epic→Feature→Story→Task)
jive_get_work_item         # Retrieve work item details with relationships
jive_update_work_item      # Update properties, status, and relationships
jive_list_work_items       # List with filtering, sorting, pagination
jive_search_work_items     # Semantic and keyword search
```

### Hierarchy & Dependencies
```bash
jive_get_work_item_children     # Get child work items (recursive option)
jive_get_work_item_dependencies # Analyze blocking dependencies
jive_validate_dependencies      # Check for circular dependencies
jive_execute_work_item          # AI-powered autonomous execution
jive_get_execution_status       # Monitor execution progress
jive_cancel_execution           # Stop and rollback execution
```

### Storage & Sync
```bash
jive_sync_file_to_database   # Sync local files to vector database
jive_sync_database_to_file   # Export database changes to files
jive_get_sync_status         # Check synchronization status
```

### Validation & Quality
```bash
jive_validate_task_completion  # Validate against acceptance criteria
jive_run_quality_gates         # Execute quality gate checks
jive_get_validation_status     # Retrieve validation results
jive_approve_completion        # Mark as approved after validation
jive_request_changes           # Request changes with feedback
```

### AI Orchestration
```bash
ai_execute           # Execute AI requests through orchestration
ai_provider_status   # Get provider health and statistics
ai_configure         # Update orchestrator configuration
```

### Search & Discovery (Full Mode Only)
```bash
jive_search_tasks        # Search tasks with advanced filtering
jive_search_content      # Cross-content-type search
jive_list_tasks          # List tasks with sorting options
jive_get_task_hierarchy  # Get hierarchical task structure
```

### Task Management (Full Mode Only)
```bash
jive_create_task   # Create development tasks
jive_update_task   # Update task properties
jive_delete_task   # Delete tasks (with subtask option)
jive_get_task      # Retrieve detailed task information
```

### Progress Tracking (Full Mode Only)
```bash
jive_track_progress      # Track entity progress (0-100%)
jive_get_progress_report # Detailed progress reports
jive_set_milestone       # Set and track milestones
jive_get_analytics       # Performance analytics and insights
```

### Workflow Execution (Full Mode Only)
```bash
jive_execute_workflow    # Execute workflows with dependencies
jive_validate_workflow   # Validate workflow structure
jive_get_workflow_status # Monitor workflow progress
jive_cancel_workflow     # Cancel running workflows
```

## Common Parameter Patterns

### Work Item Identification
All tools accept flexible identifiers:
- **UUID**: `"work-item-123e4567-e89b-12d3-a456-426614174000"`
- **Exact Title**: `"User Authentication System"`
- **Keywords**: `"auth login security"`

### Status Values
```json
// Work Item Status
["not_started", "in_progress", "completed", "blocked", "cancelled"]

// Task Status
["todo", "in_progress", "completed", "cancelled"]

// Validation Status
["pending", "in_progress", "passed", "failed", "requires_review", "approved", "rejected"]
```

### Priority Levels
```json
["low", "medium", "high", "critical"] // Work Items
["low", "medium", "high", "urgent"]   // Tasks
```

### Work Item Types (Hierarchy)
```json
["initiative", "epic", "feature", "story", "task"]
```

## Configuration

### Environment Variables
```bash
# Tool Mode Selection
export MCP_TOOL_MODE=minimal  # 16 essential tools
export MCP_TOOL_MODE=full     # 35 comprehensive tools (default)

# Logging
export JIVE_LOG_LEVEL=INFO

# Database
export JIVE_DATABASE_PATH=/path/to/lancedb

# AI Provider
export JIVE_AI_PROVIDER=anthropic
```

### Mode Comparison

| Feature | Minimal Mode | Full Mode |
|---------|--------------|----------|
| **Tools Count** | 16 | 35 |
| **Work Item CRUD** | ✅ Full | ✅ Full |
| **Basic Hierarchy** | ✅ Limited | ✅ Complete |
| **AI Orchestration** | ✅ Full | ✅ Full |
| **Storage Sync** | ✅ Full | ✅ Full |
| **Validation** | ⚠️ Basic | ✅ Comprehensive |
| **Search & Discovery** | ❌ | ✅ Advanced |
| **Task Management** | ❌ | ✅ Full |
| **Progress Tracking** | ❌ | ✅ Analytics |
| **Workflow Execution** | ❌ | ✅ Orchestration |
| **Use Case** | AI Agents | Full PM |

## Quick Start Examples

### 1. Create and Execute a Story
```json
// 1. Create Story
{
  "tool": "jive_create_work_item",
  "params": {
    "type": "story",
    "title": "User Login Feature",
    "description": "Implement secure user authentication",
    "acceptance_criteria": ["Secure login", "Password validation", "Session management"]
  }
}

// 2. Execute with AI
{
  "tool": "jive_execute_work_item",
  "params": {
    "work_item_id": "story-123",
    "execution_mode": "dependency_based",
    "agent_context": {
      "project_path": "/path/to/project",
      "environment": "development"
    }
  }
}

// 3. Monitor Progress
{
  "tool": "jive_get_execution_status",
  "params": {
    "execution_id": "exec-456",
    "include_logs": true
  }
}
```

### 2. Search and Filter Work Items
```json
// Semantic Search
{
  "tool": "jive_search_work_items",
  "params": {
    "query": "authentication security login",
    "search_type": "semantic",
    "limit": 10
  }
}

// Filtered List
{
  "tool": "jive_list_work_items",
  "params": {
    "filters": {
      "status": ["in_progress", "blocked"],
      "priority": ["high", "critical"]
    },
    "sort_by": "priority",
    "limit": 20
  }
}
```

### 3. Validation Workflow
```json
// Run Quality Gates
{
  "tool": "jive_run_quality_gates",
  "params": {
    "work_item_id": "story-123",
    "gate_ids": ["code_review", "testing", "security"],
    "execution_mode": "fail_fast"
  }
}

// Approve Completion
{
  "tool": "jive_approve_completion",
  "params": {
    "work_item_id": "story-123",
    "approver_id": "reviewer-456",
    "approval_type": "full_approval"
  }
}
```

### 4. AI Orchestration
```json
// Execute AI Request
{
  "tool": "ai_execute",
  "params": {
    "messages": [
      {"role": "user", "content": "Help implement user authentication"}
    ],
    "provider": "anthropic",
    "model": "claude-3-sonnet",
    "max_tokens": 4000,
    "execution_mode": "mcp_client_sampling"
  }
}

// Check Provider Status
{
  "tool": "ai_provider_status",
  "params": {
    "provider": "anthropic",
    "include_stats": true
  }
}
```

## Response Format

All tools return standardized JSON responses:

```json
{
  "success": true,
  "data": { /* Tool-specific data */ },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-03T10:30:00Z",
  "execution_time_ms": 150,
  "metadata": {
    "tool_name": "jive_create_work_item",
    "version": "1.0.0",
    "request_id": "req-123"
  }
}
```

## Error Handling

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Invalid work item type",
  "details": {
    "field": "type",
    "allowed_values": ["initiative", "epic", "feature", "story", "task"]
  },
  "timestamp": "2025-01-03T10:30:00Z"
}
```

## Best Practices

### 1. Work Item Hierarchy
- Follow Initiative → Epic → Feature → Story → Task structure
- Define acceptance criteria at Story level
- Estimate effort at Task level

### 2. Dependency Management
- Validate dependencies before execution
- Use dependency-based execution modes
- Monitor blocking dependencies regularly

### 3. Progress Tracking
- Update progress regularly (daily/weekly)
- Set meaningful milestones
- Use analytics for performance insights

### 4. Quality Assurance
- Implement quality gates for all work items
- Use validation tools before marking complete
- Maintain approval workflows

### 5. AI Orchestration
- Choose appropriate execution modes
- Monitor provider health
- Use context-aware agent coordination

## Troubleshooting

### Common Issues
1. **Tool Not Found**: Check `MCP_TOOL_MODE` environment variable
2. **Validation Failures**: Verify parameter types and required fields
3. **Dependency Errors**: Run `jive_validate_dependencies`
4. **Sync Issues**: Use `jive_get_sync_status` to identify conflicts
5. **AI Problems**: Check `ai_provider_status`

### Performance Tips
1. Use appropriate limits for list operations
2. Apply filters to narrow search results
3. Use pagination for large datasets
4. Cache frequently accessed work items

---

**For detailed parameter documentation, see**: `COMPREHENSIVE_MCP_TOOLS_REFERENCE.md`

**For implementation details, see**: Individual tool files in `src/mcp_jive/tools/`