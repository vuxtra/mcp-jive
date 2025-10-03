# MCP Jive Consolidated Tools Reference

**Last Updated**: 2024-12-19 | **Total Tools**: 7 | **Status**: Active

This document provides a comprehensive reference for AI agents on how to use the 7 consolidated MCP Jive tools. Each tool consolidates multiple legacy operations into a unified interface.

## Quick Reference

| Tool Name | Primary Purpose | Key Actions | Legacy Tools Replaced |
|-----------|----------------|-------------|----------------------|
| `jive_manage_work_item` | CRUD operations | create, update, delete | 8+ legacy tools |
| `jive_get_work_item` | Retrieval & listing | get by ID, search, filter | 5+ legacy tools |
| `jive_search_content` | Content search | semantic, keyword, hybrid | 3+ legacy tools |
| `jive_get_hierarchy` | Relationships & dependencies | get, add, remove, validate | 6+ legacy tools |
| `jive_execute_work_item` | Execution & workflows | execute, monitor, cancel | 5+ legacy tools |
| `jive_track_progress` | Progress & analytics | track, report, milestones | 4+ legacy tools |
| `jive_sync_data` | Storage & sync | sync, backup, restore | 5+ legacy tools |

---

## Tool 1: jive_manage_work_item

### Description
**Jive: Unified work item management - create, update, or delete work items and tasks**

This tool consolidates all CRUD (Create, Read, Update, Delete) operations for work items and tasks. It replaces multiple legacy tools for creating initiatives, epics, features, stories, and tasks.

### When to Use
- Creating new work items of any type
- Updating existing work item properties
- Deleting work items
- Managing work item metadata

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | enum | ✅ | Action to perform: "create", "update", "delete" |
| `work_item_id` | string | For update/delete | Work item identifier (UUID, title, or keywords) |
| `type` | enum | For create | Work item type: "initiative", "epic", "feature", "story", "task" |
| `title` | string | For create | Work item title |
| `description` | string | ❌ | Detailed description of the work item |
| `status` | enum | ❌ | Status: "not_started", "in_progress", "completed", "blocked", "cancelled" |
| `priority` | enum | ❌ | Priority: "low", "medium", "high", "critical" |
| `parent_id` | string | ❌ | Parent work item ID for hierarchy |

### Usage Examples

```json
// Create a new epic
{
  "action": "create",
  "type": "epic",
  "title": "User Authentication System",
  "description": "Implement comprehensive user authentication",
  "priority": "high"
}

// Update work item status
{
  "action": "update",
  "work_item_id": "auth-epic-001",
  "status": "in_progress"
}

// Delete a work item
{
  "action": "delete",
  "work_item_id": "obsolete-task-123"
}
```

---

## Tool 2: jive_get_work_item

### Description
**Jive: Unified work item retrieval - get work items by ID, title, or search criteria**

This tool handles all work item retrieval operations, including getting specific items by ID and listing items with various filters.

### When to Use
- Retrieving specific work items by ID or title
- Getting work item details with metadata
- Including child work items in responses
- Flexible search and filtering

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `work_item_id` | string | ✅ | Work item identifier (UUID, exact title, or keywords) |
| `include_children` | boolean | ❌ | Include child work items in response (default: false) |
| `include_metadata` | boolean | ❌ | Include additional metadata like progress (default: true) |
| `format` | enum | ❌ | Response format: "detailed", "summary", "minimal" (default: "detailed") |

### Usage Examples

```json
// Get detailed work item with children
{
  "work_item_id": "auth-epic-001",
  "include_children": true,
  "include_metadata": true,
  "format": "detailed"
}

// Get minimal work item info
{
  "work_item_id": "user login feature",
  "format": "minimal"
}
```

---

## Tool 3: jive_search_content

### Description
**Jive: Unified content search - search work items, tasks, and content using various methods**

This tool provides comprehensive search capabilities across all work items and content using semantic, keyword, or hybrid search methods.

### When to Use
- Finding work items by keywords or phrases
- Semantic search for related content
- Filtering search results by type, status, priority
- Discovering relevant work items

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search query - keywords, phrases, or specific terms |
| `search_type` | enum | ❌ | Search method: "semantic", "keyword", "hybrid" (default: "hybrid") |
| `filters` | object | ❌ | Optional filters for type, status, priority |
| `limit` | integer | ❌ | Maximum results to return (default: 10, max: 100) |
| `format` | enum | ❌ | Response format: "detailed", "summary", "minimal" (default: "summary") |

### Filters Object

| Filter | Type | Description |
|--------|------|-------------|
| `type` | array | Filter by work item types |
| `status` | array | Filter by status values |
| `priority` | array | Filter by priority levels |

### Usage Examples

```json
// Semantic search for authentication-related items
{
  "query": "user authentication and security",
  "search_type": "semantic",
  "limit": 20
}

// Keyword search with filters
{
  "query": "login",
  "search_type": "keyword",
  "filters": {
    "type": ["feature", "story"],
    "status": ["in_progress", "not_started"]
  }
}
```

---

## Tool 4: jive_get_hierarchy

### Description
**Jive: Unified hierarchy and dependency operations - retrieve relationships, manage dependencies, and validate hierarchy structures**

This tool manages all hierarchy and dependency operations, including parent-child relationships, dependencies, and validation.

### When to Use
- Getting work item children or parents
- Managing dependencies between work items
- Validating hierarchy structures
- Retrieving full hierarchy trees

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `work_item_id` | string | ✅ | Work item ID (UUID, exact title, or keywords) |
| `relationship_type` | enum | ✅ | Type: "children", "parents", "dependencies", "dependents", "full_hierarchy", "ancestors", "descendants" |
| `action` | enum | ❌ | Action: "get", "add_dependency", "remove_dependency", "validate" (default: "get") |
| `target_work_item_id` | string | For dependencies | Target work item ID for dependency operations |
| `dependency_type` | enum | ❌ | Dependency type: "blocks", "blocked_by", "related", "subtask_of" |
| `max_depth` | integer | ❌ | Maximum depth for hierarchy traversal (default: 5, max: 10) |
| `include_completed` | boolean | ❌ | Include completed work items (default: true) |
| `include_cancelled` | boolean | ❌ | Include cancelled work items (default: false) |
| `include_metadata` | boolean | ❌ | Include metadata like progress estimates (default: true) |

### Usage Examples

```json
// Get all children of an epic
{
  "work_item_id": "auth-epic-001",
  "relationship_type": "children",
  "include_metadata": true
}

// Add a dependency
{
  "work_item_id": "login-feature",
  "relationship_type": "dependencies",
  "action": "add_dependency",
  "target_work_item_id": "user-model-task",
  "dependency_type": "blocks"
}

// Validate dependencies
{
  "work_item_id": "auth-epic-001",
  "relationship_type": "dependencies",
  "action": "validate",
  "validation_options": {
    "check_circular": true,
    "check_missing": true
  }
}
```

---

## Tool 5: jive_execute_work_item

### Description
**Unified tool for executing work items and workflows. Supports execution, monitoring, validation, and cancellation. Can execute single work items or complex workflows with dependencies.**

This tool handles all execution-related operations for work items and workflows.

### When to Use
- Executing individual work items
- Running complex workflows with dependencies
- Monitoring execution status
- Cancelling running executions
- Validating execution readiness

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `work_item_id` | string | ✅ | Work item ID to execute (UUID, exact title, or keywords) |
| `execution_mode` | enum | ❌ | Mode: "autonomous", "guided", "validation_only", "dry_run" (default: "autonomous") |
| `action` | enum | ❌ | Action: "execute", "status", "cancel", "validate" (default: "execute") |
| `execution_id` | string | For status/cancel | Execution ID for status/cancel operations |
| `workflow_config` | object | ❌ | Configuration for workflow execution |
| `execution_context` | object | ❌ | Context and constraints for execution |

### Usage Examples

```json
// Execute a work item autonomously
{
  "work_item_id": "implement-login-api",
  "execution_mode": "autonomous"
}

// Check execution status
{
  "action": "status",
  "execution_id": "exec-12345"
}

// Cancel execution
{
  "action": "cancel",
  "execution_id": "exec-12345",
  "cancel_options": {
    "reason": "Requirements changed",
    "rollback_changes": true
  }
}
```

---

## Tool 6: jive_track_progress

### Description
**Unified tool for progress tracking and analytics. Tracks progress, generates reports, manages milestones, and provides analytics. Supports individual work items and aggregate reporting.**

This tool handles all progress tracking, reporting, and analytics operations.

### When to Use
- Tracking work item progress
- Generating progress reports
- Setting and managing milestones
- Getting analytics and insights
- Monitoring team velocity

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | enum | ✅ | Action: "track", "get_report", "set_milestone", "get_analytics", "get_status" |
| `work_item_id` | string | For tracking | Work item ID for tracking (UUID, exact title, or keywords) |
| `work_item_ids` | array | For batch ops | Multiple work item IDs for batch operations |
| `progress_data` | object | For tracking | Progress tracking data |
| `report_config` | object | For reports | Configuration for progress reports |
| `milestone_config` | object | For milestones | Configuration for milestone creation |
| `analytics_config` | object | For analytics | Configuration for analytics generation |

### Usage Examples

```json
// Track progress for a work item
{
  "action": "track",
  "work_item_id": "login-feature",
  "progress_data": {
    "progress_percentage": 75,
    "status": "in_progress",
    "notes": "API implementation complete, working on UI"
  }
}

// Generate progress report
{
  "action": "get_report",
  "report_config": {
    "entity_type": "epic",
    "time_range": {
      "period": "last_30_days"
    },
    "include_analytics": true
  }
}

// Set milestone
{
  "action": "set_milestone",
  "milestone_config": {
    "title": "Authentication MVP Complete",
    "target_date": "2024-12-31T23:59:59Z",
    "milestone_type": "release",
    "associated_tasks": ["auth-epic-001"]
  }
}
```

---

## Tool 7: jive_sync_data

### Description
**Unified tool for storage and synchronization operations. Handles file-to-database sync, database-to-file sync, backup, restore, and status monitoring. Supports various file formats and merge strategies.**

This tool manages all data storage, synchronization, backup, and restore operations.

### When to Use
- Syncing work items between files and database
- Creating backups of work item data
- Restoring from backups
- Exporting work items to files
- Importing work items from files

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | enum | ✅ | Action: "sync", "status", "backup", "restore", "validate" |
| `sync_direction` | enum | For sync | Direction: "file_to_db", "db_to_file", "bidirectional" |
| `file_path` | string | ❌ | Path to the file for synchronization |
| `file_content` | string | ❌ | Content to sync to database (for file_to_db sync) |
| `work_item_id` | string | ❌ | Work item ID for database-to-file sync |
| `work_item_ids` | array | ❌ | Multiple work item IDs for batch operations |
| `format` | enum | ❌ | File format: "json", "yaml", "markdown", "csv", "xml" (default: "json") |
| `merge_strategy` | enum | ❌ | Merge strategy: "overwrite", "merge", "append", "skip_existing", "prompt" |

### Usage Examples

```json
// Sync work items from file to database
{
  "action": "sync",
  "sync_direction": "file_to_db",
  "file_path": "./work_items.json",
  "merge_strategy": "merge"
}

// Export work items to file
{
  "action": "sync",
  "sync_direction": "db_to_file",
  "target_file_path": "./export/auth_epic.yaml",
  "work_item_ids": ["auth-epic-001"],
  "format": "yaml"
}

// Create backup
{
  "action": "backup",
  "backup_config": {
    "backup_name": "pre_release_backup",
    "include_files": true,
    "compression_level": 6
  }
}
```

---

## AI Agent Usage Guidelines

### Tool Selection Strategy

1. **Work Item CRUD**: Use `jive_manage_work_item`
2. **Getting/Finding Items**: Use `jive_get_work_item` for specific items, `jive_search_content` for discovery
3. **Relationships**: Use `jive_get_hierarchy` for parent-child and dependencies
4. **Execution**: Use `jive_execute_work_item` for running tasks and workflows
5. **Progress Tracking**: Use `jive_track_progress` for monitoring and analytics
6. **Data Management**: Use `jive_sync_data` for backup, restore, and file operations

### Best Practices

1. **Always validate work_item_id**: Use flexible identifiers (UUID, title, or keywords)
2. **Use appropriate formats**: Choose "minimal" for lists, "detailed" for single items
3. **Include metadata when needed**: Set `include_metadata: true` for comprehensive data
4. **Filter search results**: Use filters to narrow down search results
5. **Validate dependencies**: Use validation actions before making changes
6. **Track progress regularly**: Update progress data for better analytics
7. **Create backups**: Use sync tool for important data operations

### Error Handling

All tools return structured responses with:
- `success`: Boolean indicating operation success
- `error`: Error message if operation failed
- `error_code`: Specific error code for programmatic handling
- `data`: Response data for successful operations

### Performance Considerations

- Use `limit` parameters to control response size
- Choose appropriate `format` levels (minimal vs detailed)
- Use filters to reduce search scope
- Set reasonable `max_depth` for hierarchy operations
- Consider `include_completed` and `include_cancelled` flags

---

## Legacy Tool Mapping

For reference, here's how legacy tools map to the new consolidated tools:

### jive_manage_work_item replaces:
- `jive_create_initiative`
- `jive_create_epic`
- `jive_create_feature`
- `jive_create_story`
- `jive_create_task`
- `jive_update_work_item`
- `jive_delete_work_item`
- `jive_set_work_item_status`

### jive_get_work_item replaces:
- `jive_get_work_item_by_id`
- `jive_get_work_item_by_title`
- `jive_list_work_items`
- `jive_get_work_item_details`
- `jive_filter_work_items`

### jive_search_content replaces:
- `jive_search_work_items`
- `jive_search_tasks`
- `jive_search_content`

### jive_get_hierarchy replaces:
- `jive_get_work_item_children`
- `jive_get_work_item_dependencies`
- `jive_get_task_hierarchy`
- `jive_add_dependency`
- `jive_remove_dependency`
- `jive_validate_dependencies`

### jive_execute_work_item replaces:
- `jive_execute_work_item`
- `jive_execute_workflow`
- `jive_get_execution_status`
- `jive_cancel_execution`
- `jive_validate_workflow`

### jive_track_progress replaces:
- `jive_track_progress`
- `jive_get_progress_report`
- `jive_set_milestone`
- `jive_get_analytics`

### jive_sync_data replaces:
- `jive_sync_file_to_database`
- `jive_sync_database_to_file`
- `jive_get_sync_status`
- `jive_backup_data`
- `jive_restore_data`

---

**This reference document ensures AI agents can effectively use the consolidated MCP Jive tools with clear descriptions, parameters, and usage examples.**