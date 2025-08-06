# Comprehensive MCP Jive Tools Reference

**Last Updated**: 2025-01-15 | **Status**: ✅ Current | **Architecture**: Consolidated Tools

## Overview

MCP Jive provides a streamlined suite of 7 consolidated tools optimized for AI agents and autonomous development workflows. This document provides detailed information about all available tools, their parameters, usage patterns, and migration from legacy tools.

## Tool Architecture

### Consolidated Tools (7 Core Tools)
The modern MCP Jive architecture uses 7 unified tools that replace 26 legacy tools:
- **Environment Variable**: `MCP_TOOL_MODE=consolidated`
- **Focus**: AI-optimized unified operations with intelligent parameter handling
- **Use Case**: Autonomous AI agents, streamlined development workflows

### Legacy Compatibility Modes
- **Minimal Mode**: 7 consolidated + essential legacy tools for compatibility
- **Full Mode**: 7 consolidated + all 26 legacy tools for complete backward compatibility

---

## Consolidated Tools Reference

### 1. jive_manage_work_item
**Purpose**: Unified CRUD operations for all work item types (Initiative → Epic → Feature → Story → Task)

**Replaces Legacy Tools**: `jive_create_work_item`, `jive_update_work_item`, `jive_create_task`, `jive_update_task`, `jive_delete_task`

**Parameters**:
```json
{
  "action": "create|update|delete",
  "work_item_id": "string (required for update/delete)",
  "type": "initiative|epic|feature|story|task",
  "title": "string",
  "description": "string",
  "status": "not_started|in_progress|completed|blocked|cancelled",
  "priority": "low|medium|high|critical",
  "parent_id": "string (optional)",
  "tags": ["string"],
  "acceptance_criteria": ["string"],
  "effort_estimate": "number (hours)",
  "due_date": "ISO 8601 date string",
  "delete_children": "boolean (for delete action)"
}
```

**Usage Examples**:
```json
// Create a new story
{
  "action": "create",
  "type": "story",
  "title": "User Authentication System",
  "description": "Implement secure user login and registration",
  "priority": "high",
  "parent_id": "epic-123",
  "acceptance_criteria": [
    "Users can register with email and password",
    "Users can login securely",
    "Password reset functionality works"
  ],
  "effort_estimate": 8,
  "tags": ["authentication", "security"]
}

// Update work item status
{
  "action": "update",
  "work_item_id": "story-456",
  "status": "completed",
  "description": "Updated implementation with OAuth2 support"
}
```

### 2. jive_get_work_item
**Purpose**: Unified retrieval and listing with advanced filtering and flexible identification

**Replaces Legacy Tools**: `jive_get_work_item`, `jive_list_work_items`, `jive_get_task`, `jive_list_tasks`

**Parameters**:
```json
{
  "work_item_id": "string (optional - for single item)",
  "filters": {
    "type": ["initiative", "epic", "feature", "story", "task"],
    "status": ["not_started", "in_progress", "completed"],
    "priority": ["low", "medium", "high", "critical"],
    "assignee_id": "string",
    "parent_id": "string",
    "tags": ["string"]
  },
  "include_children": "boolean",
  "include_dependencies": "boolean",
  "include_metadata": "boolean",
  "sort_by": "created_date|priority|status|title",
  "sort_order": "asc|desc",
  "limit": "number",
  "offset": "number"
}
```

**Usage Examples**:
```json
// Get specific work item with relationships
{
  "work_item_id": "story-456",
  "include_children": true,
  "include_dependencies": true
}

// List high-priority tasks
{
  "filters": {
    "type": ["task"],
    "priority": ["high", "critical"],
    "status": ["not_started", "in_progress"]
  },
  "sort_by": "priority",
  "sort_order": "desc",
  "limit": 20
}
```

### 3. jive_search_content
**Purpose**: Unified search across all content types with semantic, keyword, and hybrid search capabilities

**Replaces Legacy Tools**: `jive_search_work_items`, `jive_search_tasks`, `jive_search_content`

**Parameters**:
```json
{
  "query": "string (required)",
  "search_type": "semantic|keyword|hybrid",
  "content_types": ["work_item", "task", "execution_log"],
  "filters": {
    "type": ["initiative", "epic", "feature", "story", "task"],
    "status": ["not_started", "in_progress", "completed"],
    "priority": ["low", "medium", "high", "critical"],
    "tags": ["string"]
  },
  "limit": "number",
  "include_metadata": "boolean"
}
```

**Usage Examples**:
```json
// Semantic search for authentication-related work
{
  "query": "user login security authentication",
  "search_type": "semantic",
  "content_types": ["work_item"],
  "limit": 10
}

// Hybrid search with filters
{
  "query": "API endpoint",
  "search_type": "hybrid",
  "filters": {
    "type": ["task", "story"],
    "status": ["in_progress"]
  },
  "limit": 15
}
```

### 4. jive_get_hierarchy
**Purpose**: Unified hierarchy and dependency navigation with relationship analysis

**Replaces Legacy Tools**: `jive_get_work_item_children`, `jive_get_work_item_dependencies`, `jive_validate_dependencies`, `jive_get_work_item_hierarchy`, `jive_get_task_hierarchy`, `jive_get_dependency_graph`

**Parameters**:
```json
{
  "work_item_id": "string (required)",
  "operation": "children|dependencies|hierarchy|validate_dependencies",
  "include_recursive": "boolean",
  "include_metadata": "boolean",
  "max_depth": "number",
  "direction": "up|down|both"
}
```

**Usage Examples**:
```json
// Get all children recursively
{
  "work_item_id": "epic-123",
  "operation": "children",
  "include_recursive": true,
  "max_depth": 3
}

// Validate dependencies for circular references
{
  "work_item_id": "story-456",
  "operation": "validate_dependencies",
  "include_metadata": true
}
```

### 5. jive_execute_work_item
**Purpose**: Unified execution for work items and workflows with autonomous AI capabilities

**Replaces Legacy Tools**: `jive_execute_work_item`, `jive_execute_workflow`, `jive_get_execution_status`, `jive_cancel_execution`, `jive_trigger_dependent_execution`

**Parameters**:
```json
{
  "work_item_id": "string (required)",
  "action": "start|pause|resume|cancel|status",
  "execution_mode": "autonomous|guided|manual",
  "ai_provider": "anthropic|openai|google",
  "include_dependencies": "boolean",
  "execution_options": {
    "max_retries": "number",
    "timeout_minutes": "number",
    "rollback_on_failure": "boolean"
  }
}
```

**Usage Examples**:
```json
// Start autonomous execution
{
  "work_item_id": "task-789",
  "action": "start",
  "execution_mode": "autonomous",
  "ai_provider": "anthropic",
  "include_dependencies": true,
  "execution_options": {
    "max_retries": 3,
    "timeout_minutes": 60,
    "rollback_on_failure": true
  }
}

// Check execution status
{
  "work_item_id": "task-789",
  "action": "status"
}
```

### 6. jive_track_progress
**Purpose**: Unified progress tracking, analytics, and reporting across all work items

**Replaces Legacy Tools**: `jive_get_progress_report`, `jive_track_progress`, `jive_set_milestone`, `jive_get_analytics`

**Parameters**:
```json
{
  "work_item_id": "string (optional)",
  "operation": "update|report|analytics|milestone",
  "progress_data": {
    "completion_percentage": "number (0-100)",
    "milestone_name": "string",
    "milestone_date": "ISO 8601 date"
  },
  "report_type": "summary|detailed|analytics",
  "time_range": {
    "start_date": "ISO 8601 date",
    "end_date": "ISO 8601 date"
  },
  "include_children": "boolean"
}
```

**Usage Examples**:
```json
// Update progress
{
  "work_item_id": "story-456",
  "operation": "update",
  "progress_data": {
    "completion_percentage": 75
  }
}

// Generate analytics report
{
  "operation": "analytics",
  "report_type": "detailed",
  "time_range": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-15T23:59:59Z"
  }
}
```

### 7. jive_sync_data
**Purpose**: Unified storage and synchronization with backup, export, and import capabilities

**Replaces Legacy Tools**: `jive_sync_file_to_database`, `jive_sync_database_to_file`, `jive_get_sync_status`, `jive_backup_data`, `jive_export_data`

**Parameters**:
```json
{
  "operation": "sync_to_db|sync_to_file|status|backup|export|import",
  "file_path": "string (optional)",
  "sync_options": {
    "include_metadata": "boolean",
    "overwrite_existing": "boolean",
    "backup_before_sync": "boolean"
  },
  "export_format": "json|csv|markdown",
  "filters": {
    "type": ["work_item", "execution_log"],
    "date_range": {
      "start_date": "ISO 8601 date",
      "end_date": "ISO 8601 date"
    }
  }
}
```

**Usage Examples**:
```json
// Sync database to files
{
  "operation": "sync_to_file",
  "file_path": "./exports/work_items.json",
  "sync_options": {
    "include_metadata": true,
    "backup_before_sync": true
  },
  "export_format": "json"
}

// Check sync status
{
  "operation": "status"
}
```

---

## Legacy Tool Migration

### Migration Mapping

| Legacy Tool | Consolidated Tool | Migration Notes |
|-------------|-------------------|------------------|
| `jive_create_work_item` | `jive_manage_work_item` | Use `action: "create"` |
| `jive_update_work_item` | `jive_manage_work_item` | Use `action: "update"` |
| `jive_get_work_item` | `jive_get_work_item` | Direct mapping with enhanced filters |
| `jive_list_work_items` | `jive_get_work_item` | Use without `work_item_id` parameter |
| `jive_search_work_items` | `jive_search_content` | Enhanced with semantic search |
| `jive_get_work_item_children` | `jive_get_hierarchy` | Use `operation: "children"` |
| `jive_execute_work_item` | `jive_execute_work_item` | Enhanced with AI provider options |
| `jive_get_execution_status` | `jive_execute_work_item` | Use `action: "status"` |
| `jive_sync_file_to_database` | `jive_sync_data` | Use `operation: "sync_to_db"` |
| `jive_sync_database_to_file` | `jive_sync_data` | Use `operation: "sync_to_file"` |

### Backward Compatibility

Legacy tools are automatically mapped to consolidated tools when `enable_legacy_support=true`. The mapping preserves all functionality while providing enhanced capabilities.

---

## Best Practices

### For AI Agents
1. **Use Consolidated Tools**: Prefer consolidated tools for new implementations
2. **Flexible Identification**: Work items can be identified by UUID, exact title, or keywords
3. **Batch Operations**: Use filtering and bulk operations when possible
4. **Error Handling**: Always check response status and handle errors gracefully

### Performance Optimization
1. **Limit Results**: Use `limit` and `offset` for large datasets
2. **Selective Inclusion**: Only include metadata/children when needed
3. **Appropriate Search**: Use semantic search for concept-based queries, keyword for exact matches
4. **Caching**: Leverage built-in caching for frequently accessed data

### Security Considerations
1. **Input Validation**: All parameters are validated against schemas
2. **Access Control**: Work item access is controlled by ownership and permissions
3. **Audit Trail**: All operations are logged for security and debugging
4. **Data Encryption**: Sensitive data is encrypted at rest and in transit

---

## Troubleshooting

### Common Issues

**Tool Not Found**
- Ensure `MCP_TOOL_MODE` is set correctly
- Check tool name spelling (must include `jive_` prefix)

**Parameter Validation Errors**
- Verify all required parameters are provided
- Check parameter types match schema definitions
- Ensure enum values are valid

**Performance Issues**
- Use appropriate filters to limit result sets
- Consider pagination for large datasets
- Check database health and connectivity

**Legacy Tool Compatibility**
- Enable legacy support: `enable_legacy_support=true`
- Check migration mapping for parameter changes
- Update tool calls to use consolidated equivalents

### Support Resources

- **Documentation**: `/docs/CONSOLIDATED_TOOLS_USAGE_GUIDE.md`
- **Migration Guide**: `/docs/TOOL_CONSOLIDATION_SUMMARY.md`
- **API Reference**: Built-in tool schemas and validation
- **Community**: GitHub Issues and Discussions

---

**Last Updated**: 2025-01-15 | **Version**: 2.0.0 | **Architecture**: Consolidated Tools