# Comprehensive MCP Jive Tools Reference

**Last Updated**: 2025-01-19 | **Status**: ✅ Current | **Architecture**: Consolidated Tools

## Overview

This comprehensive reference documents the 7 consolidated MCP Jive tools that replace 26 legacy tools, providing a unified, AI-optimized interface for project management and workflow automation.

## Tool Architecture

### Consolidation Benefits
The modern MCP Jive architecture uses 7 unified tools that replace 26 legacy tools:

- **73% Tool Reduction**: From 26 to 7 tools
- **50-75% Performance Improvement**: Faster response times
- **47-50% Memory Reduction**: More efficient resource usage
- **Enhanced AI Capabilities**: Optimized for autonomous agents
- **Unified Interface**: Consistent parameters and responses

## 1. jive_manage_work_item

**Purpose**: Unified CRUD operations for all work item types

**Replaces Legacy Tools**:
- `jive_create_work_item`
- `jive_update_work_item` 
- `jive_delete_work_item`
- `jive_create_task`
- `jive_update_task`

**Core Capabilities**:
- Create, update, and delete work items
- Support for all work item types (initiative, epic, feature, story, task)
- Hierarchical validation and enforcement
- Acceptance criteria management
- Progress tracking integration

**Key Parameters**:
- `action`: "create", "update", "delete"
- `work_item_id`: Flexible identifier (UUID, title, keywords)
- `type`: Work item type with hierarchy validation
- `title`, `description`: Core content fields
- `status`, `priority`: State management
- `parent_id`: Hierarchy relationships
- `acceptance_criteria`: Array of testable criteria
- `tags`: Contextual categorization

**Usage Examples**:
```json
// Create Story
{
  "action": "create",
  "type": "story",
  "title": "User Authentication System",
  "description": "Implement secure user login and registration",
  "priority": "high",
  "acceptance_criteria": [
    "Users can register with email and password",
    "Users can login securely",
    "Password reset functionality works"
  ],
  "tags": ["security", "authentication", "user-management"]
}

// Update Work Item
{
  "action": "update",
  "work_item_id": "story-123",
  "status": "in_progress",
  "progress_percentage": 45
}

// Delete Work Item
{
  "action": "delete",
  "work_item_id": "task-456",
  "delete_children": false
}
```

## 2. jive_get_work_item

**Purpose**: Unified retrieval and listing with advanced filtering

**Replaces Legacy Tools**:
- `jive_get_work_item`
- `jive_list_work_items`
- `jive_get_task`
- `jive_list_tasks`

**Core Capabilities**:
- Flexible work item identification
- Advanced filtering and sorting
- Pagination support
- Metadata inclusion control
- Hierarchical data retrieval

**Key Parameters**:
- `work_item_id`: Optional for listing mode
- `filters`: Advanced filtering options
- `sort_by`: Sorting criteria
- `limit`, `offset`: Pagination
- `include_children`: Hierarchical inclusion
- `include_metadata`: Control metadata verbosity

**Usage Examples**:
```json
// Get Specific Work Item
{
  "work_item_id": "story-123",
  "include_children": true,
  "include_metadata": true
}

// List with Filters
{
  "filters": {
    "status": ["in_progress", "blocked"],
    "priority": ["high", "critical"],
    "type": ["story", "task"]
  },
  "sort_by": "priority",
  "limit": 20
}

// Paginated Listing
{
  "limit": 50,
  "offset": 100,
  "sort_by": "created_at"
}
```

## 3. jive_search_content

**Purpose**: Unified search across all content types

**Replaces Legacy Tools**:
- `jive_search_work_items`
- `jive_search_tasks`
- `jive_search_content`

**Core Capabilities**:
- Semantic search using embeddings
- Keyword-based search
- Hybrid search algorithms
- Cross-content-type search
- Relevance scoring and ranking

**Key Parameters**:
- `query`: Search query string
- `search_type`: "semantic", "keyword", "hybrid"
- `content_types`: Types to search within
- `filters`: Additional filtering
- `limit`: Result count limit
- `min_score`: Relevance threshold

**Usage Examples**:
```json
// Semantic Search
{
  "query": "user authentication security login",
  "search_type": "semantic",
  "content_types": ["work_items", "tasks"],
  "limit": 10
}

// Keyword Search
{
  "query": "API endpoint authentication",
  "search_type": "keyword",
  "filters": {
    "status": ["in_progress", "completed"]
  }
}

// Hybrid Search
{
  "query": "database migration performance",
  "search_type": "hybrid",
  "min_score": 0.7
}
```

## 4. jive_get_hierarchy

**Purpose**: Unified hierarchy and dependency navigation

**Replaces Legacy Tools**:
- `jive_get_work_item_children`
- `jive_get_work_item_parents`
- `jive_get_work_item_dependencies`
- `jive_validate_dependencies`

**Core Capabilities**:
- Hierarchical relationship traversal
- Dependency management
- Circular dependency detection
- Relationship validation
- Multi-level hierarchy support

**Key Parameters**:
- `work_item_id`: Root item for traversal
- `relationship_type`: "children", "parents", "dependencies", "dependents"
- `action`: "get", "add_dependency", "remove_dependency", "validate"
- `target_work_item_id`: For dependency operations
- `max_depth`: Traversal depth limit
- `validation_options`: Validation configuration

**Usage Examples**:
```json
// Get Children Recursively
{
  "work_item_id": "epic-123",
  "relationship_type": "children",
  "max_depth": 3,
  "include_metadata": true
}

// Add Dependency
{
  "work_item_id": "story-456",
  "action": "add_dependency",
  "target_work_item_id": "story-123",
  "dependency_type": "blocks"
}

// Validate Dependencies
{
  "work_item_id": "epic-789",
  "action": "validate",
  "validation_options": {
    "check_circular": true,
    "check_missing": true
  }
}
```

## 5. jive_execute_work_item

**Purpose**: Unified execution for work items and workflows

**Replaces Legacy Tools**:
- `jive_execute_work_item`
- `jive_get_execution_status`
- `jive_cancel_execution`

**Core Capabilities**:
- Autonomous and guided execution modes
- Workflow orchestration
- Execution monitoring and control
- Resource management
- Rollback and recovery

**Key Parameters**:
- `work_item_id`: Item to execute
- `action`: "execute", "status", "cancel", "validate"
- `execution_mode`: "autonomous", "guided", "validation_only"
- `workflow_config`: Execution configuration
- `execution_context`: Environment and constraints
- `monitoring_config`: Progress tracking settings

**Usage Examples**:
```json
// Start Autonomous Execution
{
  "work_item_id": "task-789",
  "action": "execute",
  "execution_mode": "autonomous",
  "include_dependencies": true,
  "execution_context": {
    "environment": "development",
    "priority": "high"
  }
}

// Check Execution Status
{
  "work_item_id": "task-789",
  "action": "status",
  "execution_id": "exec-123"
}

// Cancel Execution
{
  "work_item_id": "task-789",
  "action": "cancel",
  "execution_id": "exec-123",
  "cancel_options": {
    "reason": "Requirements changed",
    "rollback_changes": true
  }
}
```

## 6. jive_track_progress

**Purpose**: Unified progress tracking and analytics

**Replaces Legacy Tools**:
- `jive_track_progress`
- `jive_get_progress_report`
- `jive_set_milestone`
- `jive_get_analytics`

**Core Capabilities**:
- Progress tracking and updates
- Milestone management
- Analytics and reporting
- Predictive insights
- Performance metrics

**Key Parameters**:
- `action`: "track", "get_report", "set_milestone", "get_analytics"
- `work_item_id`: Target item for tracking
- `progress_data`: Progress update information
- `report_config`: Report generation settings
- `milestone_config`: Milestone definition
- `analytics_config`: Analytics parameters

**Usage Examples**:
```json
// Update Progress
{
  "action": "track",
  "work_item_id": "story-123",
  "progress_data": {
    "progress_percentage": 75,
    "status": "in_progress",
    "notes": "Authentication module completed"
  }
}

// Generate Report
{
  "action": "get_report",
  "work_item_ids": ["epic-456"],
  "report_config": {
    "include_children": true,
    "time_range": "last_30_days",
    "include_analytics": true
  }
}

// Set Milestone
{
  "action": "set_milestone",
  "milestone_config": {
    "title": "MVP Release",
    "target_date": "2025-03-01",
    "associated_tasks": ["story-123", "story-456"]
  }
}
```

## 7. jive_sync_data

**Purpose**: Unified storage and synchronization

**Replaces Legacy Tools**:
- `jive_sync_to_database`
- `jive_sync_to_file`
- `jive_backup_data`

**Core Capabilities**:
- Bidirectional synchronization
- Multiple file format support
- Backup and restore operations
- Conflict resolution
- Data validation

**Key Parameters**:
- `action`: "sync", "backup", "restore", "status"
- `sync_direction`: "file_to_db", "db_to_file", "bidirectional"
- `file_path`: Source/target file path
- `format`: "json", "yaml", "markdown", "csv"
- `merge_strategy`: Conflict resolution approach
- `backup_config`: Backup settings

**Usage Examples**:
```json
// Sync File to Database
{
  "action": "sync",
  "sync_direction": "file_to_db",
  "file_path": "./project-plan.md",
  "format": "markdown",
  "merge_strategy": "merge"
}

// Create Backup
{
  "action": "backup",
  "backup_config": {
    "backup_name": "pre-migration-backup",
    "include_files": true,
    "compression_level": 6
  }
}

// Check Sync Status
{
  "action": "status",
  "file_path": "./project-plan.md"
}
```

## Legacy Tool Migration

### Migration Mapping Table

| Legacy Tool | Consolidated Tool | Migration Parameters |
|-------------|-------------------|---------------------|
| `jive_create_work_item` | `jive_manage_work_item` | `action: "create"` |
| `jive_update_work_item` | `jive_manage_work_item` | `action: "update"` |
| `jive_delete_work_item` | `jive_manage_work_item` | `action: "delete"` |
| `jive_list_work_items` | `jive_get_work_item` | Remove `work_item_id` |
| `jive_search_work_items` | `jive_search_content` | `content_types: ["work_items"]` |
| `jive_get_work_item_children` | `jive_get_hierarchy` | `relationship_type: "children"` |
| `jive_execute_work_item` | `jive_execute_work_item` | Enhanced with unified actions |
| `jive_track_progress` | `jive_track_progress` | `action: "track"` |

### Backward Compatibility Notes

- **Unified Tools**: Single optimized tool set for all implementations
- **Legacy Support**: Optional legacy tool support during migration
- **Migration Timeline**: 6-month deprecation period for legacy tools

## Best Practices

### For AI Agents
1. **Use Optimized Tools**: Leverage unified tools for better performance
2. **Leverage Action Parameters**: Use action-based operations for efficiency
3. **Apply Intelligent Filtering**: Use advanced filters to narrow results
4. **Monitor Progress**: Regularly update progress and status
5. **Validate Dependencies**: Check dependencies before execution

### For Developers
1. **Error Handling**: Implement comprehensive error handling
2. **Performance Optimization**: Use pagination and filtering
3. **Monitoring**: Set up proper logging and monitoring
4. **Testing**: Validate all tool integrations thoroughly
5. **Documentation**: Keep tool usage documented

## Security Considerations

- **Authentication**: All tools require proper authentication
- **Authorization**: Role-based access control enforced
- **Data Validation**: Input validation on all parameters
- **Audit Logging**: All operations logged for compliance
- **Rate Limiting**: API rate limits enforced

## Troubleshooting

### Common Issues
1. **Tool Not Found**: Check server configuration and tool registry
2. **Parameter Validation Errors**: Verify required fields and data types
3. **Dependency Conflicts**: Use `jive_get_hierarchy` with validation
4. **Performance Issues**: Check resource usage and apply filters
5. **Sync Failures**: Check file permissions and format compatibility

### Debug Commands
```bash
# Validate work item
jive_get_work_item --work_item_id story-123 --validate

# Check dependencies
jive_get_hierarchy --work_item_id story-123 --action validate
```

### Support Resources
- **Documentation**: Complete guides in `/docs/` directory
- **Examples**: Usage examples in each tool section
- **Quick Reference**: `/docs/quick_tools_reference.md`
- **Implementation Guide**: `/docs/CONSOLIDATED_TOOLS_IMPLEMENTATION_GUIDE.md`

---

**Last Updated**: 2025-01-19 | **Version**: 2.0.0 | **Architecture**: Consolidated Tools