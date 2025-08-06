# Quick MCP Jive Tools Reference

**Last Updated**: 2025-01-15 | **Status**: ✅ Current | **Architecture**: Consolidated Tools

## Tool Architecture Overview

| Mode | Tools Count | Description | Use Case |
|------|-------------|-------------|----------|
| **Consolidated** | 7 | AI-optimized unified tools | Recommended for all new implementations |
| **Minimal** | 7 + essential legacy | Consolidated + backward compatibility | Migration scenarios |
| **Full** | 7 + 26 legacy | Complete legacy support | Full backward compatibility |

## Consolidated Tools (7 Core Tools)

### 1. jive_manage_work_item
**Purpose**: Unified CRUD operations for all work item types  
**Actions**: `create`, `update`, `delete`  
**Replaces**: 5 legacy tools (`jive_create_work_item`, `jive_update_work_item`, `jive_create_task`, `jive_update_task`, `jive_delete_task`)

```bash
# Create work item
jive_manage_work_item --action create --type story --title "User Login"

# Update work item
jive_manage_work_item --action update --work_item_id story-123 --status in_progress

# Delete work item
jive_manage_work_item --action delete --work_item_id task-456
```

### 2. jive_get_work_item
**Purpose**: Unified retrieval and listing with advanced filtering  
**Features**: Flexible identification, advanced filters, pagination  
**Replaces**: 4 legacy tools (`jive_get_work_item`, `jive_list_work_items`, `jive_get_task`, `jive_list_tasks`)

```bash
# Get specific work item
jive_get_work_item --work_item_id story-123 --include_children

# List with filters
jive_get_work_item --filters '{"status": ["in_progress"], "priority": ["high"]}'

# Paginated listing
jive_get_work_item --limit 20 --offset 40
```

### 3. jive_search_content
**Purpose**: Unified search across all content types  
**Search Types**: `semantic`, `keyword`, `hybrid`  
**Replaces**: 3 legacy tools (`jive_search_work_items`, `jive_search_tasks`, `jive_search_content`)

```bash
# Semantic search
jive_search_content --query "authentication security" --search_type semantic

# Keyword search
jive_search_content --query "login password" --search_type keyword

# Hybrid search
jive_search_content --query "user auth" --search_type hybrid --content_types '["story", "task"]'
```

### 4. jive_get_hierarchy
**Purpose**: Hierarchy and dependency navigation  
**Operations**: `children`, `dependencies`, `hierarchy`, `validate_dependencies`  
**Replaces**: 6 legacy tools (hierarchy and dependency management)

```bash
# Get children recursively
jive_get_hierarchy --work_item_id epic-123 --operation children --include_recursive

# Get dependencies
jive_get_hierarchy --work_item_id story-456 --operation dependencies

# Validate dependencies
jive_get_hierarchy --work_item_id story-456 --operation validate_dependencies
```

### 5. jive_execute_work_item
**Purpose**: Unified execution for work items and workflows  
**Actions**: `start`, `pause`, `resume`, `cancel`, `status`  
**Replaces**: 5 legacy tools (execution and workflow management)

```bash
# Start execution
jive_execute_work_item --work_item_id story-123 --action start --execution_mode autonomous

# Check status
jive_execute_work_item --work_item_id story-123 --action status

# Pause execution
jive_execute_work_item --work_item_id story-123 --action pause
```

### 6. jive_track_progress
**Purpose**: Progress tracking, analytics, and reporting  
**Operations**: `update`, `report`, `analytics`, `milestone`  
**Replaces**: 4 legacy tools (progress and analytics)

```bash
# Update progress
jive_track_progress --work_item_id story-123 --operation update --progress_data '{"completion_percentage": 75}'

# Generate report
jive_track_progress --work_item_id epic-456 --operation report --include_children

# Get analytics
jive_track_progress --operation analytics --time_range "last_30_days"
```

### 7. jive_sync_data
**Purpose**: Storage and synchronization capabilities  
**Operations**: `sync_to_db`, `sync_to_file`, `status`, `backup`, `export`, `import`  
**Replaces**: 5 legacy tools (storage and sync)

```bash
# Sync file to database
jive_sync_data --operation sync_to_db --file_path ./project.md

# Export to file
jive_sync_data --operation sync_to_file --work_item_id story-123 --target_path ./export.json

# Check sync status
jive_sync_data --operation status --file_path ./project.md
```

## Configuration

### Environment Variables
```bash
# Tool Mode Selection
export MCP_TOOL_MODE=consolidated  # 7 unified tools (recommended)
export MCP_TOOL_MODE=minimal       # 7 + essential legacy tools
export MCP_TOOL_MODE=full          # 7 + all 26 legacy tools

# Database (LanceDB)
export LANCEDB_DATA_PATH=./data/lancedb
export LANCEDB_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# AI Providers (No longer required - using MCP client execution)

# Logging
export JIVE_LOG_LEVEL=INFO
```

### Mode Comparison

| Feature | Consolidated (7) | Minimal (7+legacy) | Full (7+all legacy) |
|---------|------------------|--------------------|-----------------|
| **Tool Count** | 7 | 7 + essential | 7 + 26 legacy |
| **Work Item CRUD** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Hierarchy Management** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Search & Discovery** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Execution & Workflows** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Progress & Analytics** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Data Synchronization** | ✅ Unified | ✅ + Legacy | ✅ + Legacy |
| **Legacy Compatibility** | ❌ | ✅ Essential | ✅ Complete |
| **Performance** | ⚡ Optimized | ⚠️ Mixed | ⚠️ Legacy overhead |
| **Maintenance** | ✅ Simplified | ⚠️ Dual support | ❌ Complex |

## Quick Start Examples

### 1. Create and Execute a Story
```json
// 1. Create Story
{
  "tool": "jive_manage_work_item",
  "params": {
    "action": "create",
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
    "action": "start",
    "execution_mode": "autonomous",
    "agent_context": {
      "project_path": "/path/to/project",
      "environment": "development"
    }
  }
}

// 3. Monitor Progress
{
  "tool": "jive_execute_work_item",
  "params": {
    "work_item_id": "story-123",
    "action": "status"
  }
}
```

### 2. Search and Filter Work Items
```json
// Semantic Search
{
  "tool": "jive_search_content",
  "params": {
    "query": "authentication security login",
    "search_type": "semantic",
    "limit": 10
  }
}

// Filtered List
{
  "tool": "jive_get_work_item",
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

### 3. Hierarchy and Dependencies
```json
// Get Children Recursively
{
  "tool": "jive_get_hierarchy",
  "params": {
    "work_item_id": "epic-123",
    "operation": "children",
    "include_recursive": true
  }
}

// Validate Dependencies
{
  "tool": "jive_get_hierarchy",
  "params": {
    "work_item_id": "story-456",
    "operation": "validate_dependencies"
  }
}
```

### 4. Progress Tracking and Analytics
```json
// Update Progress
{
  "tool": "jive_track_progress",
  "params": {
    "work_item_id": "story-123",
    "operation": "update",
    "progress_data": {
      "completion_percentage": 75,
      "notes": "Authentication module completed"
    }
  }
}

// Generate Analytics
{
  "tool": "jive_track_progress",
  "params": {
    "operation": "analytics",
    "time_range": "last_30_days",
    "metrics": ["velocity", "completion_rate"]
  }
}
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

// Validation Status
["pending", "in_progress", "passed", "failed", "requires_review", "approved", "rejected"]
```

### Priority Levels
```json
["low", "medium", "high", "critical"]
```

### Work Item Types (Hierarchy)
```json
["initiative", "epic", "feature", "story", "task"]
```

## Migration from Legacy Tools

### Quick Migration Guide

| Legacy Tool | Consolidated Tool | Migration |
|-------------|-------------------|----------|
| `jive_create_work_item` | `jive_manage_work_item` | Add `action: "create"` |
| `jive_update_work_item` | `jive_manage_work_item` | Add `action: "update"` |
| `jive_list_work_items` | `jive_get_work_item` | Remove `work_item_id` parameter |
| `jive_search_work_items` | `jive_search_content` | Enhanced with `content_types` |
| `jive_get_work_item_children` | `jive_get_hierarchy` | Add `operation: "children"` |
| `jive_get_work_item_dependencies` | `jive_get_hierarchy` | Add `operation: "dependencies"` |
| `jive_execute_work_item` | `jive_execute_work_item` | Enhanced with unified actions |
| `jive_track_progress` | `jive_track_progress` | Enhanced with operations |

### Migration Steps
1. **Assessment**: Identify current legacy tool usage
2. **Mapping**: Map legacy calls to consolidated equivalents
3. **Testing**: Validate functionality with consolidated tools
4. **Deployment**: Switch to `MCP_TOOL_MODE=consolidated`
5. **Cleanup**: Remove legacy tool dependencies

## Response Format

All tools return standardized JSON responses:

```json
{
  "success": true,
  "data": { /* Tool-specific data */ },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00Z",
  "execution_time_ms": 150,
  "metadata": {
    "tool_name": "jive_manage_work_item",
    "version": "2.0.0",
    "request_id": "req-123",
    "mode": "consolidated"
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
  "timestamp": "2025-01-15T10:30:00Z",
  "suggestions": [
    "Use 'story' for user-facing functionality",
    "Use 'task' for implementation work"
  ]
}
```

## Best Practices

### 1. Use Consolidated Tools
- Prefer consolidated tools for better performance
- Leverage unified parameter handling
- Take advantage of intelligent defaults

### 2. Work Item Hierarchy
- Follow Initiative → Epic → Feature → Story → Task structure
- Define acceptance criteria at Story level
- Estimate effort at Task level

### 3. Dependency Management
- Use `jive_get_hierarchy` to validate dependencies
- Implement dependency-based execution
- Monitor blocking dependencies regularly

### 4. Progress Tracking
- Update progress regularly using unified operations
- Set meaningful milestones
- Use analytics for performance insights

### 5. Search and Discovery
- Use semantic search for concept-based queries
- Use keyword search for exact matches
- Combine with filters for precise results

## Troubleshooting

### Common Issues
1. **Tool Not Found**: Check `MCP_TOOL_MODE` environment variable
2. **Parameter Validation**: Verify required fields and data types
3. **Dependency Errors**: Use `jive_get_hierarchy` with `validate_dependencies`
4. **Sync Issues**: Check `jive_sync_data` status operation
5. **Performance**: Switch to consolidated mode for better performance

### Performance Tips
1. Use consolidated tools for optimal performance
2. Apply filters to narrow search results
3. Use pagination for large datasets
4. Leverage semantic search for better relevance
5. Cache frequently accessed work items

### Debug Commands
```bash
# Check tool availability
echo $MCP_TOOL_MODE

# Validate work item
jive_get_work_item --work_item_id story-123 --validate

# Check dependencies
jive_get_hierarchy --work_item_id story-123 --operation validate_dependencies

# Sync status
jive_sync_data --operation status --file_path ./project.md
```

---

**For detailed parameter documentation, see**: [Comprehensive MCP Tools Reference](./COMPREHENSIVE_MCP_TOOLS_REFERENCE.md)

**For implementation details, see**: [Consolidated Tools Implementation Guide](./CONSOLIDATED_TOOLS_IMPLEMENTATION_GUIDE.md)

**For migration guidance, see**: [Tool Consolidation Summary](./TOOL_CONSOLIDATION_SUMMARY.md)