# Quick MCP Jive Tools Reference

**Last Updated**: 2025-01-19 | **Status**: ✅ Current | **Architecture**: Consolidated Tools

## Overview

Quick reference for the 7 consolidated MCP Jive tools that replace 26 legacy tools, providing 73% tool reduction with enhanced performance and AI optimization.

## Consolidated Tool Architecture

### Performance Benefits
- **73% Tool Reduction**: 26 → 7 tools
- **50-75% Faster**: Response time improvement
- **47-50% Memory**: Reduced resource usage
- **Enhanced AI**: Optimized for autonomous agents

## 1. jive_manage_work_item

**Purpose**: Unified CRUD operations for all work item types

**Key Actions**:
- `create`: Create new work items
- `update`: Modify existing work items
- `delete`: Remove work items

**Quick Examples**:
```bash
# Create Story
jive_manage_work_item --action create --type story --title "User Login" --priority high

# Update Status
jive_manage_work_item --action update --work_item_id story-123 --status in_progress

# Delete Task
jive_manage_work_item --action delete --work_item_id task-456
```

**Common Parameters**:
- `action`: "create", "update", "delete"
- `work_item_id`: UUID, title, or keywords
- `type`: "initiative", "epic", "feature", "story", "task"
- `status`: "not_started", "in_progress", "completed", "blocked"
- `priority`: "low", "medium", "high", "critical"

## 2. jive_get_work_item

**Purpose**: Unified retrieval and listing with advanced filtering

**Quick Examples**:
```bash
# Get Specific Item
jive_get_work_item --work_item_id story-123 --include_children true

# List with Filters
jive_get_work_item --filters '{"status":["in_progress"],"priority":["high"]}' --limit 20

# Paginated List
jive_get_work_item --limit 50 --offset 100 --sort_by priority
```

**Filter Options**:
- `status`: Filter by work item status
- `priority`: Filter by priority level
- `type`: Filter by work item type
- `assignee`: Filter by assigned user
- `tags`: Filter by tags

## 3. jive_search_content

**Purpose**: Unified search across all content types

**Search Types**:
- `semantic`: AI-powered semantic search
- `keyword`: Traditional keyword matching
- `hybrid`: Combined semantic + keyword

**Quick Examples**:
```bash
# Semantic Search
jive_search_content --query "user authentication security" --search_type semantic --limit 10

# Keyword Search
jive_search_content --query "API endpoint" --search_type keyword

# Filtered Search
jive_search_content --query "database" --filters '{"status":["completed"]}'
```

## 4. jive_get_hierarchy

**Purpose**: Unified hierarchy and dependency navigation

**Relationship Types**:
- `children`: Get child work items
- `parents`: Get parent work items
- `dependencies`: Get blocking dependencies
- `dependents`: Get items blocked by this
- `full_hierarchy`: Complete hierarchy tree

**Quick Examples**:
```bash
# Get Children Recursively
jive_get_hierarchy --work_item_id epic-123 --relationship_type children --max_depth 3

# Add Dependency
jive_get_hierarchy --work_item_id story-456 --action add_dependency --target_work_item_id story-123

# Validate Dependencies
jive_get_hierarchy --work_item_id epic-789 --action validate --validation_options '{"check_circular":true}'
```

## 5. jive_execute_work_item

**Purpose**: Unified execution for work items and workflows

**Execution Modes**:
- `autonomous`: Full AI-driven execution
- `guided`: Step-by-step with human oversight
- `validation_only`: Validate without executing
- `dry_run`: Test execution without changes

**Quick Examples**:
```bash
# Start Autonomous Execution
jive_execute_work_item --work_item_id task-789 --execution_mode autonomous

# Check Status
jive_execute_work_item --work_item_id task-789 --action status --execution_id exec-123

# Cancel Execution
jive_execute_work_item --work_item_id task-789 --action cancel --execution_id exec-123
```

## 6. jive_track_progress

**Purpose**: Unified progress tracking and analytics

**Actions**:
- `track`: Update progress
- `get_report`: Generate progress reports
- `set_milestone`: Create milestones
- `get_analytics`: Get analytics data

**Quick Examples**:
```bash
# Update Progress
jive_track_progress --action track --work_item_id story-123 --progress_data '{"progress_percentage":75,"status":"in_progress"}'

# Generate Report
jive_track_progress --action get_report --work_item_ids '["epic-456"]' --report_config '{"include_children":true}'

# Get Analytics
jive_track_progress --action get_analytics --analytics_config '{"analysis_type":"velocity","time_period":"last_month"}'
```

## 7. jive_sync_data

**Purpose**: Unified storage and synchronization

**Sync Directions**:
- `file_to_db`: Import from file to database
- `db_to_file`: Export from database to file
- `bidirectional`: Two-way synchronization

**Supported Formats**:
- `json`: JSON format
- `yaml`: YAML format
- `markdown`: Markdown format
- `csv`: CSV format
- `xml`: XML format

**Quick Examples**:
```bash
# Sync File to Database
jive_sync_data --action sync --sync_direction file_to_db --file_path "./plan.md" --format markdown

# Create Backup
jive_sync_data --action backup --backup_config '{"backup_name":"pre-migration","include_files":true}'

# Check Status
jive_sync_data --action status --file_path "./plan.md"
```

## Legacy Tool Consolidation

### Replaced Tools (26 → 7)

**Work Item Management** (5 → 1):
- `jive_create_work_item` → `jive_manage_work_item` (action: "create")
- `jive_update_work_item` → `jive_manage_work_item` (action: "update")
- `jive_delete_work_item` → `jive_manage_work_item` (action: "delete")
- `jive_create_task` → `jive_manage_work_item` (type: "task")
- `jive_update_task` → `jive_manage_work_item` (type: "task")

**Retrieval & Listing** (4 → 1):
- `jive_get_work_item` → `jive_get_work_item` (enhanced)
- `jive_list_work_items` → `jive_get_work_item` (no work_item_id)
- `jive_get_task` → `jive_get_work_item` (type filter)
- `jive_list_tasks` → `jive_get_work_item` (type filter)

**Search & Discovery** (3 → 1):
- `jive_search_work_items` → `jive_search_content`
- `jive_search_tasks` → `jive_search_content`
- `jive_search_content` → `jive_search_content` (enhanced)

**Hierarchy & Dependencies** (4 → 1):
- `jive_get_work_item_children` → `jive_get_hierarchy`
- `jive_get_work_item_parents` → `jive_get_hierarchy`
- `jive_get_work_item_dependencies` → `jive_get_hierarchy`
- `jive_validate_dependencies` → `jive_get_hierarchy`

**Execution & Workflow** (3 → 1):
- `jive_execute_work_item` → `jive_execute_work_item` (enhanced)
- `jive_get_execution_status` → `jive_execute_work_item`
- `jive_cancel_execution` → `jive_execute_work_item`

**Progress & Analytics** (4 → 1):
- `jive_track_progress` → `jive_track_progress` (enhanced)
- `jive_get_progress_report` → `jive_track_progress`
- `jive_set_milestone` → `jive_track_progress`
- `jive_get_analytics` → `jive_track_progress`

**Storage & Sync** (3 → 1):
- `jive_sync_to_database` → `jive_sync_data`
- `jive_sync_to_file` → `jive_sync_data`
- `jive_backup_data` → `jive_sync_data`

## Configuration

### Environment Variables
```bash
# Database Configuration
export LANCEDB_DATA_PATH="./data/lancedb"
export LANCEDB_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"

# Logging
export JIVE_LOG_LEVEL="INFO"  # DEBUG|INFO|WARNING|ERROR
```

## Quick Start Examples

### Create and Execute a Story
```bash
# 1. Create Story
jive_manage_work_item \
  --action create \
  --type story \
  --title "Implement User Dashboard" \
  --description "Create responsive user dashboard with analytics" \
  --priority high \
  --acceptance_criteria '["Dashboard loads in <2s","Mobile responsive","Shows user analytics"]'

# 2. Execute Story
jive_execute_work_item \
  --work_item_id "Implement User Dashboard" \
  --execution_mode autonomous \
  --include_dependencies true

# 3. Monitor Progress
jive_track_progress \
  --action track \
  --work_item_id "Implement User Dashboard" \
  --progress_data '{"progress_percentage":50,"status":"in_progress"}'
```

### Search and Analyze
```bash
# 1. Semantic Search
jive_search_content \
  --query "user interface dashboard analytics" \
  --search_type semantic \
  --limit 10

# 2. Get Filtered List
jive_get_work_item \
  --filters '{"status":["in_progress"],"type":["story"]}' \
  --sort_by priority \
  --limit 20

# 3. Get Hierarchy
jive_get_hierarchy \
  --work_item_id "epic-dashboard" \
  --relationship_type children \
  --max_depth 2 \
  --include_metadata true

# 4. Generate Analytics
jive_track_progress \
  --action get_analytics \
  --analytics_config '{"analysis_type":"comprehensive","time_period":"last_month"}'
```

## Common Parameter Patterns

### Work Item Identification
- **UUID**: `"550e8400-e29b-41d4-a716-446655440000"`
- **Exact Title**: `"Implement User Authentication"`
- **Keywords**: `"user auth login"`

### Status Values
**Work Item Status**:
- `not_started`, `in_progress`, `completed`, `blocked`, `cancelled`

**Validation Status**:
- `valid`, `invalid`, `warning`, `error`

### Priority Levels
- `low`, `medium`, `high`, `critical`

### Work Item Types
- `initiative` (highest level)
- `epic` (large features)
- `feature` (medium features)
- `story` (user stories)
- `task` (implementation tasks)

## Migration Guide

### Quick Migration Steps
1. **Update Environment**: Ensure unified tool mode is active
2. **Replace Tool Calls**: Use mapping table above
3. **Update Parameters**: Use action-based parameters
4. **Test Integration**: Validate all tool calls
5. **Monitor Performance**: Check improved metrics

### Migration Mapping
```bash
# Old Way
jive_create_work_item --type story --title "Feature"
jive_update_work_item --id story-123 --status completed
jive_list_work_items --status in_progress

# New Way
jive_manage_work_item --action create --type story --title "Feature"
jive_manage_work_item --action update --work_item_id story-123 --status completed
jive_get_work_item --filters '{"status":["in_progress"]}'
```

## Response Format

### Standardized JSON Response
```json
{
  "success": true,
  "data": {
    "work_item_id": "story-123",
    "title": "Feature Title",
    "status": "in_progress",
    "metadata": {
      "created_at": "2025-01-19T10:00:00Z",
      "updated_at": "2025-01-19T15:30:00Z"
    }
  },
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  },
  "execution_time_ms": 45
}
```

### Error Handling
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid work item type",
    "details": {
      "field": "type",
      "value": "invalid_type",
      "allowed_values": ["initiative", "epic", "feature", "story", "task"]
    }
  },
  "execution_time_ms": 12
}
```

## Best Practices

### Using Consolidated Tools
1. **Prefer Action Parameters**: Use action-based operations
2. **Leverage Filters**: Use advanced filtering for efficiency
3. **Batch Operations**: Process multiple items when possible
4. **Monitor Progress**: Regular status updates
5. **Validate Dependencies**: Check before execution

### Work Item Hierarchy
1. **Follow Hierarchy**: Initiative → Epic → Feature → Story → Task
2. **Clear Dependencies**: Define blocking relationships
3. **Acceptance Criteria**: Always include testable criteria
4. **Progress Tracking**: Regular updates with meaningful progress

### Dependency Management
1. **Validate Early**: Check dependencies before execution
2. **Avoid Circular**: Use validation to prevent circular dependencies
3. **Clear Relationships**: Document dependency reasons
4. **Regular Review**: Periodically review and clean up

### Progress Tracking
1. **Regular Updates**: Update progress frequently
2. **Meaningful Percentages**: Base on actual completion
3. **Status Alignment**: Keep status and percentage aligned
4. **Milestone Tracking**: Use milestones for major checkpoints

### Search & Discovery
1. **Use Semantic Search**: For concept-based queries
2. **Combine Search Types**: Use hybrid for best results
3. **Apply Filters**: Narrow results with filters
4. **Relevance Scoring**: Use min_score for quality

## Troubleshooting

### Common Issues
1. **Tool Not Found**: Check server configuration and tool registry
2. **Parameter Validation**: Verify required fields and data types
3. **Dependency Conflicts**: Use validation before execution
4. **Performance Issues**: Check resource usage and filters
5. **Search Results**: Adjust search type and filters

### Performance Tips
1. **Optimized Tools**: 50-75% performance improvement over legacy
2. **Apply Filters**: Reduce result set size
3. **Pagination**: Use limit/offset for large datasets
4. **Selective Metadata**: Include only needed metadata
5. **Batch Operations**: Process multiple items together

### Debug Commands
```bash
# Check Configuration
echo $LANCEDB_DATA_PATH

# Validate Work Item
jive_get_work_item --work_item_id story-123 --include_metadata true

# Check Dependencies
jive_get_hierarchy --work_item_id story-123 --action validate

# Test Search
jive_search_content --query "test" --search_type hybrid --limit 5
```

## Additional Resources

- **Comprehensive Reference**: `COMPREHENSIVE_MCP_TOOLS_REFERENCE.md`
- **Implementation Guide**: `CONSOLIDATED_TOOLS_IMPLEMENTATION_GUIDE.md`
- **Usage Guide**: `CONSOLIDATED_TOOLS_USAGE_GUIDE.md`
- **Migration Summary**: `TOOL_CONSOLIDATION_SUMMARY.md`

---

**Last Updated**: 2025-01-19 | **Version**: 2.0.0 | **Architecture**: Consolidated Tools