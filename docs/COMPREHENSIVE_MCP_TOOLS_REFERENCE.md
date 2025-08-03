# Comprehensive MCP Jive Tools Reference

**Last Updated**: 2025-01-03 | **Total Tools**: 35 (Full Mode) / 16 (Minimal Mode)

## Overview

MCP Jive provides a comprehensive suite of tools for agile work item management, workflow orchestration, and AI-powered development assistance. This document provides detailed information about all available tools, their parameters, usage patterns, and the problems they solve.

## Tool Modes

### Minimal Mode (16 Tools)
Optimized for AI agents with essential work item management capabilities:
- **Environment Variable**: `MCP_TOOL_MODE=minimal`
- **Focus**: Core work item CRUD operations, basic hierarchy management, essential validation
- **Use Case**: AI agents performing focused development tasks

### Full Mode (35 Tools)
Complete feature set for comprehensive project management:
- **Environment Variable**: `MCP_TOOL_MODE=full` (default)
- **Focus**: Advanced workflow orchestration, detailed analytics, comprehensive validation
- **Use Case**: Full project management, complex workflow automation, detailed reporting

---

## Core Work Item Management Tools (5 Tools)

### 1. jive_create_work_item
**Purpose**: Create new agile work items in the hierarchy (Initiative → Epic → Feature → Story → Task)

**Parameters**:
- `type` (required): `"initiative"` | `"epic"` | `"feature"` | `"story"` | `"task"`
- `title` (required): Work item title
- `description` (required): Detailed description
- `parent_id` (optional): Parent work item ID for hierarchy
- `priority` (optional): `"low"` | `"medium"` | `"high"` | `"critical"` (default: `"medium"`)
- `acceptance_criteria` (optional): Array of acceptance criteria strings
- `effort_estimate` (optional): Effort in story points or hours
- `tags` (optional): Array of categorization tags

**Usage Example**:
```json
{
  "type": "story",
  "title": "User Authentication System",
  "description": "Implement secure user login and registration",
  "parent_id": "epic-123",
  "priority": "high",
  "acceptance_criteria": [
    "Users can register with email and password",
    "Users can login securely",
    "Password reset functionality works"
  ],
  "effort_estimate": 8,
  "tags": ["authentication", "security"]
}
```

**Problems Solved**:
- Structured work breakdown in agile hierarchies
- Clear acceptance criteria definition
- Effort estimation and planning
- Work item categorization and tagging

### 2. jive_get_work_item
**Purpose**: Retrieve detailed work item information with optional related data

**Parameters**:
- `work_item_id` (required): Work item identifier (UUID, exact title, or keywords)
- `include_children` (optional): Include child work items (default: `false`)
- `include_dependencies` (optional): Include dependency information (default: `false`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "include_children": true,
  "include_dependencies": true
}
```

**Problems Solved**:
- Flexible work item identification (UUID, title, or keyword search)
- Comprehensive work item context retrieval
- Hierarchy and dependency visualization

### 3. jive_update_work_item
**Purpose**: Update work item properties, status, and relationships

**Parameters**:
- `work_item_id` (required): Work item identifier
- `updates` (required): Object containing updates:
  - `title` (optional): New title
  - `description` (optional): New description
  - `status` (optional): `"not_started"` | `"in_progress"` | `"completed"` | `"blocked"` | `"cancelled"`
  - `priority` (optional): `"low"` | `"medium"` | `"high"` | `"critical"`
  - `acceptance_criteria` (optional): Array of criteria
  - `effort_estimate` (optional): New estimate
  - `tags` (optional): Array of tags

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "updates": {
    "status": "in_progress",
    "priority": "high",
    "effort_estimate": 10
  }
}
```

**Problems Solved**:
- Real-time work item status tracking
- Dynamic priority adjustment
- Iterative refinement of requirements

### 4. jive_list_work_items
**Purpose**: List work items with advanced filtering, sorting, and pagination

**Parameters**:
- `filters` (optional): Filter object:
  - `type`: Array of work item types
  - `status`: Array of statuses
  - `priority`: Array of priorities
  - `parent_id`: Parent work item ID
  - `tags`: Array of tags
- `limit` (optional): Max items (1-1000, default: 50)
- `offset` (optional): Skip items (default: 0)
- `sort_by` (optional): `"created_at"` | `"updated_at"` | `"priority"` | `"title"` (default: `"updated_at"`)
- `sort_order` (optional): `"asc"` | `"desc"` (default: `"desc"`)

**Usage Example**:
```json
{
  "filters": {
    "status": ["in_progress", "blocked"],
    "priority": ["high", "critical"],
    "tags": ["frontend"]
  },
  "limit": 20,
  "sort_by": "priority"
}
```

**Problems Solved**:
- Efficient work item discovery
- Status-based filtering for sprint planning
- Priority-based work organization
- Large dataset pagination

### 5. jive_search_work_items
**Purpose**: Semantic and keyword search across work items

**Parameters**:
- `query` (required): Search query string
- `search_type` (optional): `"semantic"` | `"keyword"` | `"hybrid"` (default: `"semantic"`)
- `filters` (optional): Additional filters (type, status, priority)
- `limit` (optional): Max results (1-100, default: 10)

**Usage Example**:
```json
{
  "query": "user authentication login security",
  "search_type": "semantic",
  "filters": {
    "type": ["story", "task"],
    "status": ["not_started", "in_progress"]
  },
  "limit": 15
}
```

**Problems Solved**:
- Intelligent content discovery
- Semantic similarity matching
- Cross-work-item knowledge retrieval
- Context-aware search results

---

## Hierarchy Management Tools (6 Tools)

### 6. jive_get_work_item_children
**Purpose**: Retrieve child work items in the agile hierarchy

**Parameters**:
- `work_item_id` (required): Parent work item identifier
- `include_metadata` (optional): Include effort estimates and criteria (default: `true`)
- `recursive` (optional): Get all descendants (default: `false`)

**Usage Example**:
```json
{
  "work_item_id": "epic-123",
  "include_metadata": true,
  "recursive": true
}
```

**Problems Solved**:
- Hierarchy visualization and navigation
- Effort rollup calculations
- Scope understanding for epics and features

### 7. jive_get_work_item_dependencies
**Purpose**: Analyze work item dependencies and blocking relationships

**Parameters**:
- `work_item_id` (required): Work item identifier
- `include_transitive` (optional): Include dependencies of dependencies (default: `true`)
- `only_blocking` (optional): Only return currently blocking dependencies (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "include_transitive": true,
  "only_blocking": true
}
```

**Problems Solved**:
- Dependency chain analysis
- Blocking issue identification
- Critical path planning
- Risk assessment for delivery

### 8. jive_validate_dependencies
**Purpose**: Validate dependency graph for circular dependencies and consistency

**Parameters**:
- `work_item_ids` (optional): Specific work items to validate (empty for all)
- `check_circular` (optional): Check for circular dependencies (default: `true`)
- `check_missing` (optional): Check for missing references (default: `true`)
- `suggest_fixes` (optional): Suggest fixes for issues (default: `true`)

**Usage Example**:
```json
{
  "work_item_ids": ["story-456", "story-789"],
  "check_circular": true,
  "check_missing": true,
  "suggest_fixes": true
}
```

**Problems Solved**:
- Dependency graph integrity
- Circular dependency detection
- Missing reference identification
- Automated fix suggestions

### 9. jive_execute_work_item
**Purpose**: Start autonomous execution of work items through AI agent coordination

**Parameters**:
- `work_item_id` (required): Work item to execute
- `execution_mode` (optional): `"sequential"` | `"parallel"` | `"dependency_based"` (default: `"dependency_based"`)
- `agent_context` (optional): AI agent execution context:
  - `project_path`: Project directory path
  - `environment`: Execution environment
  - `constraints`: Array of execution constraints
- `validate_before_execution` (optional): Validate dependencies first (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "execution_mode": "dependency_based",
  "agent_context": {
    "project_path": "/path/to/project",
    "environment": "development",
    "constraints": ["no_breaking_changes", "maintain_test_coverage"]
  },
  "validate_before_execution": true
}
```

**Problems Solved**:
- Automated work item execution
- AI-driven development workflows
- Dependency-aware task orchestration
- Context-aware agent coordination

### 10. jive_get_execution_status
**Purpose**: Monitor real-time execution progress of work items

**Parameters**:
- `execution_id` (required): Execution identifier
- `include_logs` (optional): Include execution logs (default: `false`)
- `include_artifacts` (optional): Include generated artifacts (default: `true`)
- `include_validation_results` (optional): Include validation results (default: `true`)

**Usage Example**:
```json
{
  "execution_id": "exec-789",
  "include_logs": true,
  "include_artifacts": true,
  "include_validation_results": true
}
```

**Problems Solved**:
- Real-time execution monitoring
- Progress tracking and reporting
- Artifact and output validation
- Execution transparency

### 11. jive_cancel_execution
**Purpose**: Stop and rollback work item execution

**Parameters**:
- `execution_id` (required): Execution to cancel
- `reason` (optional): Cancellation reason
- `rollback_changes` (optional): Rollback changes made (default: `true`)
- `force` (optional): Force cancellation even if rollback fails (default: `false`)

**Usage Example**:
```json
{
  "execution_id": "exec-789",
  "reason": "Requirements changed",
  "rollback_changes": true,
  "force": false
}
```

**Problems Solved**:
- Execution control and safety
- Change rollback capabilities
- Risk mitigation for failed executions
- Clean state recovery

---

## Storage Sync Tools (3 Tools)

### 12. jive_sync_file_to_database
**Purpose**: Synchronize local task files to the vector database

**Parameters**:
- `file_path` (required): Path relative to `.jivedev/tasks/`
- `file_content` (required): JSON or YAML content
- `merge_strategy` (optional): `"auto_merge"` | `"file_wins"` | `"database_wins"` | `"manual_resolution"` (default: `"auto_merge"`)
- `validate_only` (optional): Only validate without syncing (default: `false`)

**Usage Example**:
```json
{
  "file_path": "features/user-auth.json",
  "file_content": "{\"title\": \"User Authentication\", \"status\": \"in_progress\"}",
  "merge_strategy": "auto_merge",
  "validate_only": false
}
```

**Problems Solved**:
- File-database synchronization
- Conflict resolution strategies
- Data consistency maintenance
- Validation before sync

### 13. jive_sync_database_to_file
**Purpose**: Export database changes to local task files

**Parameters**:
- `work_item_id` (required): Work item to sync
- `target_file_path` (optional): Target file path
- `format` (optional): `"json"` | `"yaml"` (default: `"json"`)
- `merge_strategy` (optional): Conflict resolution strategy
- `create_backup` (optional): Create backup before overwriting (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "target_file_path": "stories/auth-system.yaml",
  "format": "yaml",
  "create_backup": true
}
```

**Problems Solved**:
- Database-to-file export
- Multiple format support
- Backup and safety mechanisms
- Bidirectional synchronization

### 14. jive_get_sync_status
**Purpose**: Check synchronization status and conflicts

**Parameters**:
- `file_path` (optional): Specific file to check
- `work_item_id` (optional): Specific work item to check
- `include_conflicts` (optional): Include conflict details (default: `true`)
- `check_all` (optional): Check all tracked files (default: `false`)

**Usage Example**:
```json
{
  "file_path": "features/user-auth.json",
  "include_conflicts": true,
  "check_all": false
}
```

**Problems Solved**:
- Sync status monitoring
- Conflict identification
- Data integrity verification
- Comprehensive sync auditing

---

## Validation Tools (5 Tools)

### 15. jive_validate_task_completion
**Purpose**: Validate work item completion against acceptance criteria

**Parameters**:
- `work_item_id` (required): Work item to validate
- `validation_type` (optional): `"acceptance_criteria"` | `"code_review"` | `"testing"` | `"security"` | `"performance"` | `"documentation"` | `"compliance"` | `"custom"` (default: `"acceptance_criteria"`)
- `acceptance_criteria` (optional): Array of criteria objects:
  - `criterion`: Criteria description
  - `met`: Boolean indicating if met
  - `evidence`: Supporting evidence
  - `notes`: Additional notes
- `custom_checks` (optional): Array of custom validation checks
- `auto_approve_threshold` (optional): Auto-approval percentage (0-100, default: 95)
- `validator_id` (optional): Validator identifier

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "validation_type": "acceptance_criteria",
  "acceptance_criteria": [
    {
      "criterion": "Users can register with email",
      "met": true,
      "evidence": "Registration form implemented and tested",
      "notes": "Email validation included"
    }
  ],
  "auto_approve_threshold": 95
}
```

**Problems Solved**:
- Systematic completion validation
- Quality gate enforcement
- Evidence-based approval
- Automated validation workflows

### 16. jive_run_quality_gates
**Purpose**: Execute quality gate checks for work items

**Parameters**:
- `work_item_id` (required): Work item to check
- `gate_ids` (optional): Specific quality gates to run
- `execution_mode` (optional): `"sequential"` | `"parallel"` | `"fail_fast"` (default: `"sequential"`)
- `timeout_minutes` (optional): Timeout in minutes (1-480, default: 60)
- `context` (optional): Execution context:
  - `environment`: Target environment
  - `branch`: Git branch
  - `commit_hash`: Commit identifier
  - `test_data`: Test data object
- `notify_on_completion` (optional): Send notifications (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "gate_ids": ["code_review", "testing", "security"],
  "execution_mode": "fail_fast",
  "context": {
    "environment": "staging",
    "branch": "feature/user-auth",
    "commit_hash": "abc123"
  }
}
```

**Problems Solved**:
- Automated quality assurance
- Multi-gate validation orchestration
- Context-aware quality checks
- Configurable execution strategies

### 17. jive_get_validation_status
**Purpose**: Retrieve validation results and approval status

**Parameters**:
- `work_item_ids` (optional): Array of work item IDs
- `validation_types` (optional): Filter by validation types
- `status_filter` (optional): Filter by status: `"pending"` | `"in_progress"` | `"passed"` | `"failed"` | `"requires_review"` | `"approved"` | `"rejected"`
- `include_details` (optional): Include detailed results (default: `true`)
- `include_history` (optional): Include validation history (default: `false`)
- `group_by` (optional): `"work_item"` | `"validation_type"` | `"status"` | `"validator"` (default: `"work_item"`)

**Usage Example**:
```json
{
  "work_item_ids": ["story-456", "story-789"],
  "status_filter": ["passed", "failed"],
  "include_details": true,
  "group_by": "status"
}
```

**Problems Solved**:
- Validation status tracking
- Quality metrics reporting
- Historical validation analysis
- Multi-dimensional result grouping

### 18. jive_approve_completion
**Purpose**: Mark work items as approved after validation

**Parameters**:
- `work_item_id` (required): Work item to approve
- `validation_id` (optional): Specific validation to approve
- `approver_id` (required): Approver identifier
- `approval_type` (optional): `"full_approval"` | `"conditional_approval"` | `"partial_approval"` (default: `"full_approval"`)
- `conditions` (optional): Array of conditions for conditional approval
- `approval_notes` (optional): Approval notes
- `expires_at` (optional): Approval expiration date (ISO format)
- `auto_proceed` (optional): Auto-proceed to next step (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "approver_id": "user-123",
  "approval_type": "conditional_approval",
  "conditions": ["Fix security vulnerability", "Add unit tests"],
  "approval_notes": "Good work, minor issues to address",
  "auto_proceed": false
}
```

**Problems Solved**:
- Formal approval workflows
- Conditional approval management
- Approval audit trails
- Workflow progression control

### 19. jive_request_changes
**Purpose**: Request changes with specific feedback for work items

**Parameters**:
- `work_item_id` (required): Work item requiring changes
- `validation_id` (optional): Failed validation ID
- `reviewer_id` (required): Reviewer identifier
- `change_requests` (required): Array of change request objects:
  - `category`: `"functionality"` | `"code_quality"` | `"testing"` | `"documentation"` | `"security"` | `"performance"` | `"design"` | `"other"`
  - `severity`: `"critical"` | `"major"` | `"minor"` | `"suggestion"`
  - `description`: Change description
  - `location`: Location of issue
  - `suggested_fix`: Suggested solution
  - `blocking`: Whether change blocks progress
- `overall_feedback` (optional): Overall feedback summary
- `priority` (optional): `"low"` | `"medium"` | `"high"` | `"urgent"` (default: `"medium"`)
- `due_date` (optional): Due date for changes (ISO format)
- `reassign_to` (optional): Reassign to specific person
- `notify_stakeholders` (optional): Notify stakeholders (default: `true`)

**Usage Example**:
```json
{
  "work_item_id": "story-456",
  "reviewer_id": "reviewer-123",
  "change_requests": [
    {
      "category": "security",
      "severity": "critical",
      "description": "Password validation is insufficient",
      "location": "auth/validation.py:45",
      "suggested_fix": "Implement stronger password requirements",
      "blocking": true
    }
  ],
  "priority": "high",
  "notify_stakeholders": true
}
```

**Problems Solved**:
- Structured change request management
- Categorized feedback collection
- Severity-based prioritization
- Stakeholder communication

---

## AI Orchestration Tools (3 Tools)

### 20. ai_execute
**Purpose**: Execute AI model requests through the orchestration system

**Parameters**:
- `messages` (required): Array of conversation messages:
  - `role`: `"user"` | `"assistant"` | `"system"`
  - `content`: Message content
- `provider` (optional): `"anthropic"` | `"openai"` | `"google"`
- `model` (optional): Specific model name
- `system_prompt` (optional): System prompt
- `max_tokens` (optional): Maximum tokens (1-8000)
- `temperature` (optional): Temperature (0.0-2.0)
- `execution_mode` (optional): `"mcp_client_sampling"` | `"direct_api"` | `"hybrid"`
- `tools` (optional): Available tools array
- `metadata` (optional): Additional metadata

**Usage Example**:
```json
{
  "messages": [
    {"role": "user", "content": "Help me implement user authentication"}
  ],
  "provider": "anthropic",
  "model": "claude-3-sonnet",
  "max_tokens": 4000,
  "temperature": 0.7,
  "execution_mode": "mcp_client_sampling"
}
```

**Problems Solved**:
- Multi-provider AI orchestration
- Execution mode flexibility
- Tool-enabled AI interactions
- Provider abstraction

### 21. ai_provider_status
**Purpose**: Get status and health information for AI providers

**Parameters**:
- `provider` (optional): Specific provider to check
- `include_stats` (optional): Include usage statistics (default: `true`)

**Usage Example**:
```json
{
  "provider": "anthropic",
  "include_stats": true
}
```

**Problems Solved**:
- Provider health monitoring
- Usage statistics tracking
- Service availability checking
- Performance metrics collection

### 22. ai_configure
**Purpose**: Update AI orchestrator configuration settings

**Parameters**:
- `execution_mode` (optional): Default execution mode
- `default_provider` (optional): Default AI provider
- `max_tokens` (optional): Default maximum tokens (1-8000)
- `temperature` (optional): Default temperature (0.0-2.0)
- `enable_rate_limiting` (optional): Enable/disable rate limiting

**Usage Example**:
```json
{
  "execution_mode": "hybrid",
  "default_provider": "anthropic",
  "max_tokens": 4000,
  "temperature": 0.8,
  "enable_rate_limiting": true
}
```

**Problems Solved**:
- Dynamic configuration management
- Runtime behavior adjustment
- Performance optimization
- Provider preference management

---

## Search and Discovery Tools (4 Tools)

### 23. jive_search_tasks
**Purpose**: Search tasks by various criteria with advanced filtering

**Parameters**:
- `query` (optional): Search query text
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority
- `tags` (optional): Array of tags (any match)
- `created_after` (optional): Filter by creation date (ISO format)
- `created_before` (optional): Filter by creation date (ISO format)
- `limit` (optional): Max results (1-100, default: 20)

**Usage Example**:
```json
{
  "query": "authentication security",
  "status": "in_progress",
  "priority": "high",
  "tags": ["frontend", "security"],
  "limit": 15
}
```

**Problems Solved**:
- Multi-criteria task discovery
- Time-based filtering
- Tag-based categorization
- Flexible search capabilities

### 24. jive_search_content
**Purpose**: Search across all content types (tasks, work items, etc.)

**Parameters**:
- `query` (required): Search query text
- `content_types` (optional): Array of content types: `"task"` | `"work_item"` | `"search_index"` (default: `["task", "work_item"]`)
- `limit` (optional): Max results (1-100, default: 20)
- `include_score` (optional): Include relevance scores (default: `false`)

**Usage Example**:
```json
{
  "query": "user interface design patterns",
  "content_types": ["task", "work_item"],
  "limit": 25,
  "include_score": true
}
```

**Problems Solved**:
- Cross-content-type search
- Relevance scoring
- Unified content discovery
- Search result ranking

### 25. jive_list_tasks
**Purpose**: List tasks with filtering and sorting options

**Parameters**:
- `status` (optional): Filter by status: `"todo"` | `"in_progress"` | `"completed"` | `"cancelled"`
- `priority` (optional): Filter by priority: `"low"` | `"medium"` | `"high"` | `"urgent"`
- `parent_id` (optional): Filter by parent task ID
- `sort_by` (optional): `"created_at"` | `"updated_at"` | `"title"` | `"priority"` | `"due_date"` (default: `"created_at"`)
- `sort_order` (optional): `"asc"` | `"desc"` (default: `"desc"`)
- `limit` (optional): Max results (1-100, default: 20)
- `offset` (optional): Skip results (default: 0)

**Usage Example**:
```json
{
  "status": "in_progress",
  "priority": "high",
  "sort_by": "priority",
  "sort_order": "desc",
  "limit": 30
}
```

**Problems Solved**:
- Systematic task listing
- Multi-field sorting
- Hierarchical filtering
- Pagination support

### 26. jive_get_task_hierarchy
**Purpose**: Get hierarchical structure of tasks from a root task

**Parameters**:
- `root_task_id` (optional): Root task ID (null for top-level tasks)
- `max_depth` (optional): Maximum hierarchy depth (1-10, default: 5)
- `include_completed` (optional): Include completed tasks (default: `true`)
- `include_cancelled` (optional): Include cancelled tasks (default: `false`)

**Usage Example**:
```json
{
  "root_task_id": "epic-123",
  "max_depth": 3,
  "include_completed": true,
  "include_cancelled": false
}
```

**Problems Solved**:
- Hierarchy visualization
- Scope understanding
- Depth-controlled navigation
- Status-based filtering

---

## Task Management Tools (4 Tools)

### 27. jive_create_task
**Purpose**: Create a new development task

**Parameters**:
- `title` (required): Task title
- `description` (optional): Task description
- `priority` (optional): `"low"` | `"medium"` | `"high"` | `"urgent"` (default: `"medium"`)
- `status` (optional): `"todo"` | `"in_progress"` | `"completed"` | `"cancelled"` (default: `"todo"`)
- `tags` (optional): Array of categorization tags
- `due_date` (optional): Due date (ISO format)
- `parent_id` (optional): Parent task ID for hierarchy

**Usage Example**:
```json
{
  "title": "Implement password validation",
  "description": "Add strong password requirements with validation",
  "priority": "high",
  "status": "todo",
  "tags": ["security", "validation"],
  "due_date": "2025-01-15T00:00:00Z",
  "parent_id": "story-456"
}
```

**Problems Solved**:
- Granular task creation
- Hierarchical task organization
- Priority and deadline management
- Task categorization

### 28. jive_update_task
**Purpose**: Update an existing development task

**Parameters**:
- `task_id` (required): Task ID to update
- `title` (optional): Updated title
- `description` (optional): Updated description
- `priority` (optional): Updated priority
- `status` (optional): Updated status
- `tags` (optional): Updated tags
- `due_date` (optional): Updated due date

**Usage Example**:
```json
{
  "task_id": "task-789",
  "status": "in_progress",
  "priority": "urgent",
  "due_date": "2025-01-10T00:00:00Z"
}
```

**Problems Solved**:
- Task status tracking
- Dynamic priority adjustment
- Deadline management
- Progress monitoring

### 29. jive_delete_task
**Purpose**: Delete a task and optionally its subtasks

**Parameters**:
- `task_id` (required): Task ID to delete
- `delete_subtasks` (optional): Delete all subtasks (default: `false`)

**Usage Example**:
```json
{
  "task_id": "task-789",
  "delete_subtasks": true
}
```

**Problems Solved**:
- Task cleanup and removal
- Hierarchical deletion
- Data consistency maintenance
- Scope-controlled deletion

### 30. jive_get_task
**Purpose**: Retrieve detailed task information

**Parameters**:
- `task_id` (required): Task ID to retrieve
- `include_subtasks` (optional): Include subtask information (default: `false`)

**Usage Example**:
```json
{
  "task_id": "task-789",
  "include_subtasks": true
}
```

**Problems Solved**:
- Detailed task inspection
- Hierarchical context retrieval
- Comprehensive task information
- Subtask relationship understanding

---

## Progress Tracking Tools (4 Tools)

### 31. jive_track_progress
**Purpose**: Track progress of tasks, workflows, or projects

**Parameters**:
- `entity_id` (required): ID of entity to track
- `entity_type` (required): `"task"` | `"workflow"` | `"project"`
- `progress_percentage` (required): Progress percentage (0-100)
- `status` (optional): `"not_started"` | `"in_progress"` | `"on_track"` | `"behind_schedule"` | `"ahead_of_schedule"` | `"completed"` | `"blocked"` | `"cancelled"`
- `notes` (optional): Progress update notes
- `estimated_completion` (optional): Estimated completion date (ISO format)
- `blockers` (optional): Array of current blockers
- `auto_calculate_status` (optional): Auto-calculate status (default: `true`)

**Usage Example**:
```json
{
  "entity_id": "story-456",
  "entity_type": "task",
  "progress_percentage": 75,
  "status": "on_track",
  "notes": "Authentication module nearly complete",
  "estimated_completion": "2025-01-12T00:00:00Z",
  "blockers": ["Waiting for security review"]
}
```

**Problems Solved**:
- Granular progress tracking
- Status-based monitoring
- Blocker identification
- Timeline estimation

### 32. jive_get_progress_report
**Purpose**: Get detailed progress reports for entities

**Parameters**:
- `entity_ids` (optional): Array of entity IDs (empty for all)
- `entity_type` (optional): `"task"` | `"workflow"` | `"project"` | `"all"` (default: `"all"`)
- `time_range` (optional): Time range object:
  - `start_date`: Start date (ISO format)
  - `end_date`: End date (ISO format)
- `include_history` (optional): Include progress history (default: `true`)
- `include_analytics` (optional): Include analytics and trends (default: `false`)
- `group_by` (optional): `"entity_type"` | `"status"` | `"date"` | `"none"` (default: `"entity_type"`)

**Usage Example**:
```json
{
  "entity_ids": ["story-456", "epic-123"],
  "entity_type": "task",
  "time_range": {
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-01-31T23:59:59Z"
  },
  "include_analytics": true,
  "group_by": "status"
}
```

**Problems Solved**:
- Comprehensive progress reporting
- Historical trend analysis
- Multi-entity comparison
- Time-based filtering

### 33. jive_set_milestone
**Purpose**: Set and track project milestones

**Parameters**:
- `title` (required): Milestone title
- `description` (optional): Detailed description
- `milestone_type` (optional): `"task_completion"` | `"project_phase"` | `"deadline"` | `"review_point"` | `"delivery"` | `"custom"` (default: `"custom"`)
- `target_date` (required): Target completion date (ISO format)
- `associated_tasks` (optional): Array of associated task IDs
- `success_criteria` (optional): Array of success criteria
- `priority` (optional): `"low"` | `"medium"` | `"high"` | `"critical"` (default: `"medium"`)

**Usage Example**:
```json
{
  "title": "Authentication System Complete",
  "description": "All authentication features implemented and tested",
  "milestone_type": "project_phase",
  "target_date": "2025-01-20T00:00:00Z",
  "associated_tasks": ["story-456", "story-789"],
  "success_criteria": [
    "All authentication tests pass",
    "Security review completed",
    "Documentation updated"
  ],
  "priority": "high"
}
```

**Problems Solved**:
- Milestone definition and tracking
- Success criteria establishment
- Task-milestone association
- Priority-based milestone management

### 34. jive_get_analytics
**Purpose**: Get analytics and insights on progress and performance

**Parameters**:
- `analysis_type` (optional): `"overview"` | `"trends"` | `"performance"` | `"bottlenecks"` | `"predictions"` | `"milestones"` (default: `"overview"`)
- `time_period` (optional): `"last_week"` | `"last_month"` | `"last_quarter"` | `"last_year"` | `"all_time"` | `"custom"` (default: `"last_month"`)
- `custom_date_range` (optional): Custom date range object (required if time_period is "custom")
- `entity_filter` (optional): Filter object:
  - `entity_type`: Entity type filter
  - `status`: Array of statuses
  - `entity_ids`: Array of entity IDs
- `include_predictions` (optional): Include predictive analytics (default: `false`)
- `detail_level` (optional): `"summary"` | `"detailed"` | `"comprehensive"` (default: `"detailed"`)

**Usage Example**:
```json
{
  "analysis_type": "performance",
  "time_period": "last_quarter",
  "entity_filter": {
    "entity_type": "task",
    "status": ["completed", "in_progress"]
  },
  "include_predictions": true,
  "detail_level": "comprehensive"
}
```

**Problems Solved**:
- Performance analytics
- Trend identification
- Bottleneck analysis
- Predictive insights

---

## Workflow Execution Tools (4 Tools)

### 35. jive_execute_workflow
**Purpose**: Execute a workflow with defined tasks and dependencies

**Parameters**:
- `workflow_name` (required): Workflow name
- `tasks` (required): Array of task objects:
  - `id` (required): Task ID
  - `title` (required): Task title
  - `description`: Task description
  - `dependencies`: Array of dependency IDs
  - `estimated_duration`: Duration in minutes
  - `priority`: Task priority
- `execution_mode` (optional): `"sequential"` | `"parallel"` | `"dependency_based"` (default: `"dependency_based"`)
- `auto_start` (optional): Start execution immediately (default: `true`)

**Usage Example**:
```json
{
  "workflow_name": "User Authentication Implementation",
  "tasks": [
    {
      "id": "task-1",
      "title": "Design authentication schema",
      "dependencies": [],
      "estimated_duration": 120,
      "priority": "high"
    },
    {
      "id": "task-2",
      "title": "Implement login endpoint",
      "dependencies": ["task-1"],
      "estimated_duration": 180,
      "priority": "high"
    }
  ],
  "execution_mode": "dependency_based",
  "auto_start": true
}
```

**Problems Solved**:
- Workflow orchestration
- Dependency-based execution
- Task coordination
- Automated workflow management

---

## Tool Response Format

All tools return responses in a standardized JSON format:

```json
{
  "success": true|false,
  "data": {...},
  "message": "Human-readable message",
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

Errors are returned with detailed information:

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Invalid work item type: 'invalid_type'",
  "details": {
    "field": "type",
    "allowed_values": ["initiative", "epic", "feature", "story", "task"]
  },
  "timestamp": "2025-01-03T10:30:00Z"
}
```

## Configuration

### Environment Variables
- `MCP_TOOL_MODE`: `minimal` | `full` (default: `full`)
- `JIVE_LOG_LEVEL`: `DEBUG` | `INFO` | `WARNING` | `ERROR`
- `JIVE_DATABASE_PATH`: Path to LanceDB database
- `JIVE_AI_PROVIDER`: Default AI provider

### Tool Categories by Mode

**Minimal Mode (16 Tools)**:
- Core Work Item Management: 5 tools
- Basic Hierarchy Management: 3 tools
- Essential Storage Sync: 3 tools
- Basic Validation: 2 tools
- AI Orchestration: 3 tools

**Full Mode (35 Tools)**:
- All Minimal Mode tools: 16 tools
- Extended Hierarchy Management: 6 tools
- Complete Storage Sync: 3 tools
- Comprehensive Validation: 5 tools
- Search and Discovery: 4 tools
- Task Management: 4 tools
- Progress Tracking: 4 tools
- Workflow Execution: 4 tools

## Best Practices

### 1. Work Item Hierarchy
- Use Initiative → Epic → Feature → Story → Task hierarchy
- Maintain clear parent-child relationships
- Define acceptance criteria at Story level
- Estimate effort at Task level

### 2. Dependency Management
- Validate dependencies before execution
- Use `jive_validate_dependencies` regularly
- Implement dependency-based execution modes
- Monitor blocking dependencies

### 3. Progress Tracking
- Update progress regularly using `jive_track_progress`
- Set meaningful milestones with `jive_set_milestone`
- Use analytics for performance insights
- Track blockers and resolution times

### 4. Quality Assurance
- Implement quality gates for all work items
- Use validation tools before marking complete
- Maintain approval workflows
- Document change requests with specific feedback

### 5. AI Orchestration
- Choose appropriate execution modes
- Monitor provider health and performance
- Use context-aware agent coordination
- Implement proper error handling

## Integration Examples

### Creating a Complete Feature
```bash
# 1. Create Epic
jive_create_work_item {
  "type": "epic",
  "title": "User Management System",
  "description": "Complete user management with authentication and authorization"
}

# 2. Create Feature under Epic
jive_create_work_item {
  "type": "feature",
  "title": "User Authentication",
  "parent_id": "epic-123",
  "acceptance_criteria": ["Secure login", "Password reset", "Session management"]
}

# 3. Create Stories under Feature
jive_create_work_item {
  "type": "story",
  "title": "User Login",
  "parent_id": "feature-456",
  "effort_estimate": 5
}

# 4. Execute with AI coordination
jive_execute_work_item {
  "work_item_id": "story-789",
  "execution_mode": "dependency_based",
  "agent_context": {
    "project_path": "/path/to/project",
    "environment": "development"
  }
}

# 5. Track progress
jive_track_progress {
  "entity_id": "story-789",
  "entity_type": "task",
  "progress_percentage": 75,
  "status": "on_track"
}

# 6. Validate completion
jive_validate_task_completion {
  "work_item_id": "story-789",
  "validation_type": "acceptance_criteria"
}

# 7. Approve completion
jive_approve_completion {
  "work_item_id": "story-789",
  "approver_id": "reviewer-123",
  "approval_type": "full_approval"
}
```

### Workflow Orchestration
```bash
# 1. Create workflow
jive_execute_workflow {
  "workflow_name": "Feature Development Pipeline",
  "tasks": [
    {"id": "design", "title": "Design Review", "dependencies": []},
    {"id": "implement", "title": "Implementation", "dependencies": ["design"]},
    {"id": "test", "title": "Testing", "dependencies": ["implement"]},
    {"id": "deploy", "title": "Deployment", "dependencies": ["test"]}
  ],
  "execution_mode": "dependency_based"
}

# 2. Monitor workflow
jive_get_workflow_status {
  "workflow_id": "workflow-123",
  "include_task_details": true,
  "include_timeline": true
}

# 3. Get analytics
jive_get_analytics {
  "analysis_type": "performance",
  "time_period": "last_month",
  "include_predictions": true
}
```

## Troubleshooting

### Common Issues

1. **Tool Not Found**
   - Check `MCP_TOOL_MODE` environment variable
   - Verify tool is available in current mode
   - Restart MCP server after configuration changes

2. **Validation Failures**
   - Check parameter types and required fields
   - Verify work item IDs exist
   - Use flexible identifiers (UUID, title, or keywords)

3. **Dependency Errors**
   - Run `jive_validate_dependencies` to check for circular dependencies
   - Verify all referenced work items exist
   - Check dependency chain completeness

4. **Sync Issues**
   - Use `jive_get_sync_status` to identify conflicts
   - Choose appropriate merge strategies
   - Ensure file paths are relative to `.jivedev/tasks/`

5. **AI Orchestration Problems**
   - Check provider status with `ai_provider_status`
   - Verify API keys and configuration
   - Monitor rate limits and quotas

### Performance Optimization

1. **Use Appropriate Limits**
   - Set reasonable limits for list operations
   - Use pagination for large datasets
   - Filter results to reduce response size

2. **Optimize Search Queries**
   - Use specific search terms
   - Apply filters to narrow results
   - Choose appropriate search types (semantic vs keyword)

3. **Batch Operations**
   - Group related operations
   - Use bulk validation where possible
   - Minimize individual API calls

4. **Caching Strategy**
   - Cache frequently accessed work items
   - Use sync tools for offline access
   - Implement local data persistence

---

## Conclusion

The MCP Jive tool suite provides comprehensive capabilities for agile project management, workflow orchestration, and AI-powered development assistance. With 35 tools in full mode and 16 essential tools in minimal mode, it supports everything from simple task management to complex multi-agent workflow coordination.

Key benefits:
- **Structured Work Management**: Hierarchical work item organization with clear relationships
- **Intelligent Automation**: AI-powered execution and validation
- **Flexible Integration**: Multiple execution modes and provider support
- **Comprehensive Tracking**: Detailed progress monitoring and analytics
- **Quality Assurance**: Built-in validation and approval workflows
- **Scalable Architecture**: Configurable tool modes for different use cases

For additional support and documentation, refer to the individual tool implementation files and the MCP Jive project documentation.