# Comprehensive MCP Jive Tool Test Suite

**Status**: 🧪 READY FOR TESTING | **Priority**: Critical | **Last Updated**: 2025-01-29  
**Test Mode**: Full Mode (35 Tools) | **Test Coverage**: 100% | **Execution**: End-to-End

## Overview

This comprehensive test suite validates all 35 MCP tools available in full mode across 8 functional categories. Each test includes specific prompts, expected parameters, and validation criteria for systematic end-to-end testing.

## Test Environment Setup

### Prerequisites
- ✅ MCP Jive server running in **full mode** (`MCP_TOOL_MODE=full`)
- ✅ LanceDB initialized with all required tables
- ✅ All 35 tools registered and available
- ✅ Clean test environment (no existing work items)

### ⚠️ CRITICAL: MCP Server Restart Requirements

**IMPORTANT**: After making ANY changes to the MCP server code, configuration, or tool implementations:

1. **You MUST ask the user to restart the MCP server** before testing changes
2. **The MCP server for AI Agent Chat runs in a separate instance** inside the editor
3. **Only the user has access** to restart this MCP server instance
4. **Changes will NOT be visible** in the AI Agent Chat until restart

**Restart Reminder Protocol**:
```
🔄 MCP SERVER RESTART REQUIRED

Changes made to:
- [List specific changes made]

Please restart your MCP server to see these changes in the AI Agent Chat.
The server runs in a separate instance that only you can control.
```

### Verification Commands
```bash
# Verify full mode is enabled
echo $MCP_TOOL_MODE  # Should output: full

# Check server status
curl http://localhost:8000/health

# Verify tool count
curl http://localhost:8000/tools | jq '.tools | length'  # Should output: 35
```

---

## Category 1: Task Management Tools (4 Tools)

### Test 1.1: jive_create_task
**Purpose**: Create development tasks with metadata

**Test Prompt**:
```
Use jive_create_task to create:
1. A high-priority task titled "Implement user authentication API" with description "Create REST API endpoints for user login, logout, and token validation" and tags ["backend", "security", "api"]
2. A medium-priority task titled "Design user dashboard wireframes" with description "Create wireframes for the main user dashboard interface" and tags ["frontend", "design", "ui"]
3. An urgent task titled "Fix critical security vulnerability" with description "Patch SQL injection vulnerability in user input validation" and tags ["security", "bugfix", "critical"]
```

**Expected Parameters**:
- `title` (required): string
- `description`: string
- `priority`: enum ["low", "medium", "high", "urgent"]
- `status`: enum ["todo", "in_progress", "completed", "cancelled"]
- `tags`: array of strings
- `due_date`: ISO date-time string
- `parent_id`: string (UUID)

**Validation Criteria**:
- ✅ Task created with unique UUID
- ✅ All metadata properly stored
- ✅ Created/updated timestamps set
- ✅ Response includes task details

### Test 1.2: jive_update_task
**Purpose**: Update existing task properties

**Test Prompt**:
```
Use jive_update_task to:
1. Update the authentication API task status to "in_progress"
2. Change the dashboard wireframes task priority to "high"
3. Add a due date of "2025-02-15T17:00:00Z" to the security vulnerability task
4. Update the security task description to include "URGENT: Affects user data security"
```

**Expected Parameters**:
- `task_id` (required): string (UUID)
- `title`: string
- `description`: string
- `priority`: enum ["low", "medium", "high", "urgent"]
- `status`: enum ["todo", "in_progress", "completed", "cancelled"]
- `tags`: array of strings
- `due_date`: ISO date-time string

**Validation Criteria**:
- ✅ Task properties updated correctly
- ✅ Updated timestamp modified
- ✅ Original creation data preserved
- ✅ Response confirms changes

### Test 1.3: jive_get_task
**Purpose**: Retrieve detailed task information

**Test Prompt**:
```
Use jive_get_task to:
1. Retrieve complete details for the authentication API task
2. Get the security vulnerability task with subtask information included
3. Fetch the dashboard wireframes task details
```

**Expected Parameters**:
- `task_id` (required): string (UUID)
- `include_subtasks`: boolean (default: false)

**Validation Criteria**:
- ✅ Complete task details returned
- ✅ All metadata fields present
- ✅ Subtasks included when requested
- ✅ Proper error handling for invalid IDs

### Test 1.4: jive_delete_task
**Purpose**: Remove tasks and handle dependencies

**Test Prompt**:
```
Use jive_delete_task to:
1. Delete the dashboard wireframes task (simple deletion)
2. Create a parent task with subtasks, then delete with delete_subtasks=true
3. Attempt to delete a non-existent task (error handling test)
```

**Expected Parameters**:
- `task_id` (required): string (UUID)
- `delete_subtasks`: boolean (default: false)

**Validation Criteria**:
- ✅ Task successfully removed
- ✅ Subtasks handled according to parameter
- ✅ Dependencies properly cleaned up
- ✅ Appropriate error messages for invalid operations

---

## Category 2: Search and Discovery Tools (4 Tools)

### Test 2.1: jive_search_tasks
**Purpose**: Search tasks by various criteria

**Test Prompt**:
```
Use jive_search_tasks to:
1. Search for tasks containing "authentication" in title or description
2. Find all high-priority tasks with status "in_progress"
3. Search for tasks with tags containing "security"
4. Find tasks created after "2025-01-29T00:00:00Z" with limit 10
5. Search for urgent tasks with priority filter
```

**Expected Parameters**:
- `query`: string (search text)
- `status`: enum ["todo", "in_progress", "completed", "cancelled"]
- `priority`: enum ["low", "medium", "high", "urgent"]
- `tags`: array of strings
- `created_after`: ISO date-time string
- `created_before`: ISO date-time string
- `limit`: integer (1-100, default: 20)

**Validation Criteria**:
- ✅ Relevant results returned
- ✅ Filters applied correctly
- ✅ Results within specified limit
- ✅ Search ranking by relevance

### Test 2.2: jive_search_content
**Purpose**: Search across all content types

**Test Prompt**:
```
Use jive_search_content to:
1. Search for "API" across all content types with relevance scores
2. Search for "security" in tasks and work items only
3. Perform a broad search for "user" with limit 15
4. Search for "dashboard" with include_score=true
```

**Expected Parameters**:
- `query` (required): string
- `content_types`: array ["task", "work_item", "search_index"] (default: ["task", "work_item"])
- `limit`: integer (1-100, default: 20)
- `include_score`: boolean (default: false)

**Validation Criteria**:
- ✅ Cross-content search functionality
- ✅ Content type filtering works
- ✅ Relevance scores included when requested
- ✅ Results span multiple content types

### Test 2.3: jive_list_tasks
**Purpose**: List tasks with filtering and sorting

**Test Prompt**:
```
Use jive_list_tasks to:
1. List all tasks sorted by priority (descending)
2. Get top-level tasks (parent_id=null) sorted by created_at
3. List completed tasks with limit 5
4. Get tasks sorted by due_date (ascending) with offset 10
5. List all in_progress tasks sorted by updated_at
```

**Expected Parameters**:
- `status`: enum ["todo", "in_progress", "completed", "cancelled"]
- `priority`: enum ["low", "medium", "high", "urgent"]
- `parent_id`: string (UUID, null for top-level)
- `sort_by`: enum ["created_at", "updated_at", "title", "priority", "due_date"] (default: "created_at")
- `sort_order`: enum ["asc", "desc"] (default: "desc")
- `limit`: integer (1-100, default: 20)
- `offset`: integer (minimum: 0, default: 0)

**Validation Criteria**:
- ✅ Proper filtering by status/priority
- ✅ Correct sorting implementation
- ✅ Pagination with limit/offset
- ✅ Hierarchical filtering works

### Test 2.4: jive_get_task_hierarchy
**Purpose**: Retrieve hierarchical task structure

**Test Prompt**:
```
Use jive_get_task_hierarchy to:
1. Get complete hierarchy starting from a root task with max_depth=3
2. Retrieve all top-level tasks (root_task_id=null)
3. Get hierarchy including completed tasks but excluding cancelled
4. Fetch deep hierarchy with max_depth=5 including all task types
```

**Expected Parameters**:
- `root_task_id`: string (UUID, null for top-level)
- `max_depth`: integer (1-10, default: 5)
- `include_completed`: boolean (default: true)
- `include_cancelled`: boolean (default: false)

**Validation Criteria**:
- ✅ Hierarchical structure preserved
- ✅ Depth limiting works correctly
- ✅ Status filtering applied
- ✅ Parent-child relationships maintained

---

## Category 3: Workflow Execution Tools (4 Tools)

### Test 3.1: jive_execute_workflow
**Purpose**: Execute workflows with task dependencies

**Test Prompt**:
```
Use jive_execute_workflow to create and execute:
1. A "User Authentication Workflow" with 3 sequential tasks:
   - Task A: "Design auth schema" (no dependencies)
   - Task B: "Implement auth API" (depends on A)
   - Task C: "Add auth tests" (depends on B)
2. A parallel workflow "Frontend Development" with 2 independent tasks
3. A dependency-based workflow with complex task relationships
```

**Expected Parameters**:
- `workflow_name` (required): string
- `description`: string
- `tasks` (required): array of task objects with id, title, description, dependencies, estimated_duration, priority
- `execution_mode`: enum ["sequential", "parallel", "dependency_based"] (default: "dependency_based")
- `auto_start`: boolean (default: true)

**Validation Criteria**:
- ✅ Workflow created and started
- ✅ Task dependencies respected
- ✅ Execution mode applied correctly
- ✅ Progress tracking initiated

### Test 3.2: jive_validate_workflow
**Purpose**: Validate workflow structure and dependencies

**Test Prompt**:
```
Use jive_validate_workflow to:
1. Validate a workflow with circular dependencies (should fail)
2. Check a workflow with missing dependency references
3. Validate a properly structured workflow (should pass)
4. Test validation with check_circular_dependencies=false
```

**Expected Parameters**:
- `tasks` (required): array of task objects with id, title, dependencies
- `check_circular_dependencies`: boolean (default: true)
- `check_missing_dependencies`: boolean (default: true)

**Validation Criteria**:
- ✅ Circular dependency detection
- ✅ Missing dependency identification
- ✅ Validation passes for valid workflows
- ✅ Detailed error reporting

### Test 3.3: jive_get_workflow_status
**Purpose**: Monitor workflow execution progress

**Test Prompt**:
```
Use jive_get_workflow_status to:
1. Get status of the authentication workflow with task details
2. Check workflow progress with timeline included
3. Monitor a running workflow without task details
4. Get status of a completed workflow
```

**Expected Parameters**:
- `workflow_id` (required): string (UUID)
- `include_task_details`: boolean (default: true)
- `include_timeline`: boolean (default: false)

**Validation Criteria**:
- ✅ Current workflow status returned
- ✅ Task details included when requested
- ✅ Timeline information available
- ✅ Progress percentages accurate

### Test 3.4: jive_cancel_workflow
**Purpose**: Cancel running workflows

**Test Prompt**:
```
Use jive_cancel_workflow to:
1. Cancel a running workflow with reason "Requirements changed"
2. Force cancel a workflow that has active tasks
3. Attempt to cancel an already completed workflow
4. Cancel with detailed reason and force=false
```

**Expected Parameters**:
- `workflow_id` (required): string (UUID)
- `reason`: string
- `force`: boolean (default: false)

**Validation Criteria**:
- ✅ Workflow cancellation successful
- ✅ Running tasks handled appropriately
- ✅ Cancellation reason recorded
- ✅ Force parameter respected

---

## Category 4: Progress Tracking Tools (4 Tools)

### Test 4.1: jive_track_progress
**Purpose**: Track progress of tasks, workflows, and projects

**Test Prompt**:
```
Use jive_track_progress to:
1. Track a task at 25% completion with status "in_progress"
2. Update a workflow to 75% with status "on_track" and estimated completion date
3. Mark a project as "behind_schedule" at 40% with blockers listed
4. Track progress with auto_calculate_status=false
```

**Expected Parameters**:
- `entity_id` (required): string (UUID)
- `entity_type` (required): enum ["task", "workflow", "project"]
- `progress_percentage` (required): number (0-100)
- `status`: enum ["not_started", "in_progress", "on_track", "behind_schedule", "ahead_of_schedule", "completed", "blocked", "cancelled"]
- `notes`: string
- `estimated_completion`: ISO date-time string
- `blockers`: array of strings
- `auto_calculate_status`: boolean (default: true)

**Validation Criteria**:
- ✅ Progress tracking recorded
- ✅ Status calculation works
- ✅ Blockers and notes stored
- ✅ Timeline estimates updated

### Test 4.2: jive_get_progress_report
**Purpose**: Generate detailed progress reports

**Test Prompt**:
```
Use jive_get_progress_report to:
1. Get progress report for all entities with history included
2. Generate report for specific entity IDs with analytics
3. Create time-ranged report for last week
4. Get report grouped by status with detailed analytics
```

**Expected Parameters**:
- `entity_ids`: array of strings (empty for all)
- `entity_type`: enum ["task", "workflow", "project", "all"] (default: "all")
- `time_range`: object with start_date and end_date
- `include_history`: boolean (default: true)
- `include_analytics`: boolean (default: false)
- `group_by`: enum ["entity_type", "status", "date", "none"] (default: "entity_type")

**Validation Criteria**:
- ✅ Comprehensive progress data
- ✅ Historical tracking included
- ✅ Analytics and trends calculated
- ✅ Proper grouping applied

### Test 4.3: jive_set_milestone
**Purpose**: Set and track project milestones

**Test Prompt**:
```
Use jive_set_milestone to:
1. Create a "Beta Release" milestone with target date and success criteria
2. Set a "Code Review" milestone with associated tasks
3. Create a critical "Security Audit" milestone
4. Set a custom milestone with detailed description
```

**Expected Parameters**:
- `title` (required): string
- `description`: string
- `milestone_type`: enum ["task_completion", "project_phase", "deadline", "review_point", "delivery", "custom"] (default: "custom")
- `target_date` (required): ISO date-time string
- `associated_tasks`: array of strings (UUIDs)
- `success_criteria`: array of strings
- `priority`: enum ["low", "medium", "high", "critical"] (default: "medium")

**Validation Criteria**:
- ✅ Milestone created successfully
- ✅ Target dates and criteria stored
- ✅ Task associations maintained
- ✅ Priority levels respected

### Test 4.4: jive_get_analytics
**Purpose**: Get analytics and insights on progress

**Test Prompt**:
```
Use jive_get_analytics to:
1. Get overview analytics for the last month
2. Analyze performance trends with predictions included
3. Identify bottlenecks in current projects
4. Get comprehensive milestone analytics
```

**Expected Parameters**:
- `analysis_type`: enum ["overview", "trends", "performance", "bottlenecks", "predictions", "milestones"] (default: "overview")
- `time_period`: enum ["last_week", "last_month", "last_quarter", "last_year", "all_time", "custom"] (default: "last_month")
- `custom_date_range`: object with start_date and end_date
- `entity_filter`: object with entity_type, status, entity_ids
- `include_predictions`: boolean (default: false)
- `detail_level`: enum ["summary", "detailed", "comprehensive"] (default: "detailed")

**Validation Criteria**:
- ✅ Analytics data generated
- ✅ Trends and patterns identified
- ✅ Predictions included when requested
- ✅ Filtering applied correctly

---

## Category 5: Workflow Engine Tools (6 Tools)

### Test 5.1: jive_get_work_item_children
**Purpose**: Get child work items in hierarchy

**Test Prompt**:
```
Use jive_get_work_item_children to:
1. Get direct children of an epic (recursive=false)
2. Get all descendants of an initiative (recursive=true)
3. Retrieve children with metadata included
4. Test with work item that has no children
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID, title, or keywords)
- `include_metadata`: boolean (default: true)
- `recursive`: boolean (default: false)

**Validation Criteria**:
- ✅ Child relationships returned
- ✅ Recursive traversal works
- ✅ Metadata included when requested
- ✅ Empty results handled gracefully

### Test 5.2: jive_get_work_item_dependencies
**Purpose**: Get dependencies that block work items

**Test Prompt**:
```
Use jive_get_work_item_dependencies to:
1. Get blocking dependencies for a story
2. Retrieve transitive dependencies (dependencies of dependencies)
3. Get only currently blocking dependencies
4. Test with work item that has no dependencies
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID, title, or keywords)
- `include_transitive`: boolean (default: true)
- `only_blocking`: boolean (default: true)

**Validation Criteria**:
- ✅ Dependency relationships identified
- ✅ Transitive dependencies included
- ✅ Blocking status accurate
- ✅ Dependency chains traced

### Test 5.3: jive_validate_dependencies
**Purpose**: Validate dependency graph for circular dependencies

**Test Prompt**:
```
Use jive_validate_dependencies to:
1. Validate a set of work items with no circular dependencies
2. Test validation with circular dependency (should fail)
3. Check for missing dependency references
4. Validate with suggested fixes enabled
```

**Expected Parameters**:
- `work_item_ids`: array of strings (empty for all)
- `check_circular`: boolean (default: true)
- `check_missing`: boolean (default: true)
- `suggest_fixes`: boolean (default: true)

**Validation Criteria**:
- ✅ Circular dependencies detected
- ✅ Missing references identified
- ✅ Validation passes for valid graphs
- ✅ Fix suggestions provided

### Test 5.4: jive_execute_work_item
**Purpose**: Start autonomous execution of work items

**Test Prompt**:
```
Use jive_execute_work_item to:
1. Execute a story with dependency validation
2. Start parallel execution of multiple features
3. Execute with custom agent context
4. Start execution with validation disabled
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID, title, or keywords)
- `execution_mode`: enum ["sequential", "parallel", "dependency_based"] (default: "dependency_based")
- `agent_context`: object with project_path, environment, constraints
- `validate_before_execution`: boolean (default: true)

**Validation Criteria**:
- ✅ Execution started successfully
- ✅ Dependencies validated first
- ✅ Agent context applied
- ✅ Execution tracking initiated

### Test 5.5: jive_get_execution_status
**Purpose**: Monitor real-time execution progress

**Test Prompt**:
```
Use jive_get_execution_status to:
1. Monitor execution with logs included
2. Check status with artifacts information
3. Get validation results against acceptance criteria
4. Monitor multiple executions
```

**Expected Parameters**:
- `execution_id` (required): string (UUID)
- `include_logs`: boolean (default: false)
- `include_artifacts`: boolean (default: true)
- `include_validation_results`: boolean (default: true)

**Validation Criteria**:
- ✅ Real-time status updates
- ✅ Execution logs available
- ✅ Artifacts tracked
- ✅ Validation results included

### Test 5.6: jive_cancel_execution
**Purpose**: Stop and rollback work item execution

**Test Prompt**:
```
Use jive_cancel_execution to:
1. Cancel execution with rollback enabled
2. Force cancel without rollback
3. Cancel with detailed reason
4. Attempt to cancel completed execution
```

**Expected Parameters**:
- `execution_id` (required): string (UUID)
- `reason`: string
- `rollback_changes`: boolean (default: true)
- `force`: boolean (default: false)

**Validation Criteria**:
- ✅ Execution cancelled successfully
- ✅ Rollback performed when requested
- ✅ Cancellation reason recorded
- ✅ Force parameter respected

---

## Category 6: Storage Sync Tools (3 Tools)

### Test 6.1: jive_sync_file_to_database
**Purpose**: Sync local task metadata to vector database

**Test Prompt**:
```
Use jive_sync_file_to_database to:
1. Sync a JSON task file with auto_merge strategy
2. Sync YAML content with file_wins strategy
3. Perform validation-only sync (validate_only=true)
4. Sync with manual_resolution for conflicts
```

**Expected Parameters**:
- `file_path` (required): string (relative to .jivedev/tasks/)
- `file_content` (required): string (JSON or YAML)
- `merge_strategy`: enum ["auto_merge", "file_wins", "database_wins", "manual_resolution"] (default: "auto_merge")
- `validate_only`: boolean (default: false)

**Validation Criteria**:
- ✅ File content synced to database
- ✅ Merge strategy applied correctly
- ✅ Validation-only mode works
- ✅ Conflict resolution handled

### Test 6.2: jive_sync_database_to_file
**Purpose**: Sync database changes to local task files

**Test Prompt**:
```
Use jive_sync_database_to_file to:
1. Sync work item to JSON format with backup
2. Sync to YAML format without backup
3. Sync with database_wins merge strategy
4. Sync multiple work items to files
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID)
- `target_file_path`: string (relative to .jivedev/tasks/)
- `format`: enum ["json", "yaml"] (default: "json")
- `merge_strategy`: enum ["auto_merge", "file_wins", "database_wins", "manual_resolution"] (default: "auto_merge")
- `create_backup`: boolean (default: true)

**Validation Criteria**:
- ✅ Database content synced to file
- ✅ Format conversion accurate
- ✅ Backup created when requested
- ✅ Merge conflicts handled

### Test 6.3: jive_get_sync_status
**Purpose**: Check synchronization status of task metadata

**Test Prompt**:
```
Use jive_get_sync_status to:
1. Check status of specific file path
2. Get status for specific work item ID
3. Check all tracked files (check_all=true)
4. Get detailed conflict information
```

**Expected Parameters**:
- `file_path`: string (specific file to check)
- `work_item_id`: string (specific work item to check)
- `include_conflicts`: boolean (default: true)
- `check_all`: boolean (default: false)

**Validation Criteria**:
- ✅ Sync status accurately reported
- ✅ Conflicts identified and detailed
- ✅ File/database consistency checked
- ✅ Comprehensive status for all files

---

## Category 7: Validation Tools (5 Tools)

### Test 7.1: jive_validate_task_completion
**Purpose**: Validate task completion against acceptance criteria

**Test Prompt**:
```
Use jive_validate_task_completion to:
1. Validate task with acceptance criteria validation
2. Perform code review validation
3. Run security validation checks
4. Validate with custom checks and auto-approval threshold
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID)
- `validation_type`: enum ["acceptance_criteria", "code_review", "testing", "security", "performance", "documentation", "compliance", "custom"] (default: "acceptance_criteria")
- `acceptance_criteria`: array of criterion objects
- `custom_checks`: array of check objects
- `auto_approve_threshold`: number (0-100, default: 95)
- `validator_id`: string

**Validation Criteria**:
- ✅ Validation performed against criteria
- ✅ Custom checks executed
- ✅ Auto-approval threshold respected
- ✅ Validation results detailed

### Test 7.2: jive_run_quality_gates
**Purpose**: Execute quality gate checks for work items

**Test Prompt**:
```
Use jive_run_quality_gates to:
1. Run all quality gates for a work item
2. Execute specific gate IDs in parallel
3. Run gates with fail_fast execution mode
4. Execute with custom context and timeout
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID)
- `gate_ids`: array of strings (empty for all)
- `execution_mode`: enum ["sequential", "parallel", "fail_fast"] (default: "sequential")
- `timeout_minutes`: integer (1-480, default: 60)
- `context`: object with environment, branch, commit_hash, test_data
- `notify_on_completion`: boolean (default: true)

**Validation Criteria**:
- ✅ Quality gates executed
- ✅ Execution mode respected
- ✅ Timeout handling works
- ✅ Context applied correctly

### Test 7.3: jive_get_validation_status
**Purpose**: Retrieve validation results and approval status

**Test Prompt**:
```
Use jive_get_validation_status to:
1. Get validation status for multiple work items
2. Filter by specific validation types
3. Get status with history included
4. Retrieve status grouped by validator
```

**Expected Parameters**:
- `work_item_ids`: array of strings
- `validation_types`: array of strings
- `status_filter`: array of enum ["pending", "in_progress", "passed", "failed", "requires_review", "approved", "rejected"]
- `include_details`: boolean (default: true)
- `include_history`: boolean (default: false)
- `group_by`: enum ["work_item", "validation_type", "status", "validator"] (default: "work_item")

**Validation Criteria**:
- ✅ Validation status retrieved
- ✅ Filtering applied correctly
- ✅ History included when requested
- ✅ Grouping works as specified

### Test 7.4: jive_approve_completion
**Purpose**: Mark work items as approved after validation

**Test Prompt**:
```
Use jive_approve_completion to:
1. Give full approval to a completed work item
2. Provide conditional approval with conditions
3. Grant partial approval with expiration date
4. Approve with auto-proceed to next workflow step
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID)
- `validation_id`: string (optional)
- `approver_id` (required): string
- `approval_type`: enum ["full_approval", "conditional_approval", "partial_approval"] (default: "full_approval")
- `conditions`: array of strings
- `approval_notes`: string
- `expires_at`: ISO date-time string
- `auto_proceed`: boolean (default: true)

**Validation Criteria**:
- ✅ Approval recorded successfully
- ✅ Approval type respected
- ✅ Conditions and notes stored
- ✅ Auto-proceed functionality works

### Test 7.5: jive_request_changes
**Purpose**: Request changes with specific feedback

**Test Prompt**:
```
Use jive_request_changes to:
1. Request critical functionality changes
2. Request code quality improvements
3. Request changes with reassignment
4. Request urgent security fixes
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID)
- `validation_id`: string (optional)
- `reviewer_id` (required): string
- `change_requests` (required): array of change request objects with category, severity, description, location, suggested_fix, blocking
- `overall_feedback`: string
- `priority`: enum ["low", "medium", "high", "urgent"] (default: "medium")
- `due_date`: ISO date-time string
- `reassign_to`: string
- `notify_stakeholders`: boolean (default: true)

**Validation Criteria**:
- ✅ Change requests recorded
- ✅ Feedback and priority set
- ✅ Reassignment handled
- ✅ Stakeholder notifications sent

---

## Category 8: Client Tools (5 Tools)

### Test 8.1: jive_create_work_item
**Purpose**: Create agile work items in hierarchy

**Test Prompt**:
```
Use jive_create_work_item to create a complete agile hierarchy:
1. Initiative: "Digital Platform Modernization" (high priority)
2. Epic: "User Management System" (under the initiative)
3. Feature: "User Registration" (under the epic)
4. Story: "As a user, I want to register with email" (under the feature)
5. Task: "Implement email validation" (under the story)
```

**Expected Parameters**:
- `type` (required): enum ["initiative", "epic", "feature", "story", "task"]
- `title` (required): string
- `description`: string
- `parent_id`: string (UUID)
- `priority`: enum ["low", "medium", "high", "critical"] (default: "medium")
- `acceptance_criteria`: array of strings
- `effort_estimate`: number
- `tags`: array of strings

**Validation Criteria**:
- ✅ Work items created in hierarchy
- ✅ Parent-child relationships established
- ✅ All metadata properly stored
- ✅ Acceptance criteria included

### Test 8.2: jive_get_work_item
**Purpose**: Retrieve work item details by ID

**Test Prompt**:
```
Use jive_get_work_item to:
1. Get initiative details with children included
2. Retrieve epic with dependencies shown
3. Get story details by exact title match
4. Fetch task using keyword search
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID, title, or keywords)
- `include_children`: boolean (default: false)
- `include_dependencies`: boolean (default: false)

**Validation Criteria**:
- ✅ Work item details retrieved
- ✅ Flexible identifier resolution
- ✅ Children included when requested
- ✅ Dependencies shown when requested

### Test 8.3: jive_update_work_item
**Purpose**: Update work item properties

**Test Prompt**:
```
Use jive_update_work_item to:
1. Update story status to "in_progress"
2. Change epic priority to "critical"
3. Add acceptance criteria to a feature
4. Update effort estimate for a task
```

**Expected Parameters**:
- `work_item_id` (required): string (UUID, title, or keywords)
- `title`: string
- `description`: string
- `status`: string
- `priority`: enum ["low", "medium", "high", "critical"]
- `acceptance_criteria`: array of strings
- `effort_estimate`: number
- `tags`: array of strings

**Validation Criteria**:
- ✅ Properties updated correctly
- ✅ Flexible identifier resolution
- ✅ Updated timestamp modified
- ✅ Change history maintained

### Test 8.4: jive_list_work_items
**Purpose**: List work items with filtering

**Test Prompt**:
```
Use jive_list_work_items to:
1. List all epics and features
2. Get high-priority work items
3. List in-progress stories
4. Get work items sorted by effort estimate
```

**Expected Parameters**:
- `item_type`: array of strings
- `status`: string
- `priority`: enum ["low", "medium", "high", "critical"]
- `parent_id`: string (UUID)
- `sort_by`: enum ["created_at", "updated_at", "title", "priority", "effort_estimate"] (default: "created_at")
- `sort_order`: enum ["asc", "desc"] (default: "desc")
- `limit`: integer (1-100, default: 20)
- `offset`: integer (minimum: 0, default: 0)

**Validation Criteria**:
- ✅ Filtering by type and status
- ✅ Priority filtering works
- ✅ Sorting implementation correct
- ✅ Pagination with limit/offset

### Test 8.5: jive_search_work_items
**Purpose**: Search work items semantically

**Test Prompt**:
```
Use jive_search_work_items to:
1. Search for "authentication" across all work items
2. Find work items related to "user interface"
3. Search for "security" with high priority filter
4. Semantic search for "payment processing"
```

**Expected Parameters**:
- `query` (required): string
- `item_type`: array of strings
- `status`: string
- `priority`: enum ["low", "medium", "high", "critical"]
- `limit`: integer (1-100, default: 20)
- `include_score`: boolean (default: false)

**Validation Criteria**:
- ✅ Semantic search functionality
- ✅ Relevance ranking works
- ✅ Filtering applied correctly
- ✅ Search scores included when requested

---

## Integration Test Scenarios

### Scenario 1: Complete Agile Workflow
**Purpose**: Test end-to-end agile development workflow

**Test Steps**:
1. Create initiative → epic → feature → story → task hierarchy
2. Add dependencies between work items
3. Execute work items with validation
4. Track progress and set milestones
5. Run quality gates and approve completion
6. Sync all changes to files

### Scenario 2: Complex Dependency Management
**Purpose**: Test advanced dependency handling

**Test Steps**:
1. Create multiple work items with complex dependencies
2. Validate dependency graph
3. Execute workflow with dependency-based execution
4. Handle circular dependency detection
5. Resolve dependency conflicts

### Scenario 3: Multi-User Collaboration
**Purpose**: Test concurrent operations and conflict resolution

**Test Steps**:
1. Multiple users creating work items simultaneously
2. Concurrent updates to same work item
3. Parallel workflow executions
4. Conflict resolution in sync operations
5. Validation and approval by different users

### Scenario 4: Performance and Scale Testing
**Purpose**: Test system performance under load

**Test Steps**:
1. Create 100+ work items rapidly
2. Execute multiple workflows simultaneously
3. Perform complex searches across large datasets
4. Generate comprehensive analytics reports
5. Sync large numbers of files

---

## Validation Checklist

### For Each Tool Test:
- [ ] Tool executes without errors
- [ ] All required parameters validated
- [ ] Optional parameters work correctly
- [ ] Response format matches expected schema
- [ ] Error handling provides meaningful messages
- [ ] Performance is within acceptable limits (< 5 seconds)
- [ ] Side effects are properly managed
- [ ] Data consistency maintained across operations
- [ ] Logging captures important events
- [ ] Memory usage remains stable

### For Integration Tests:
- [ ] Cross-tool interactions work correctly
- [ ] Data flows properly between tools
- [ ] Complex workflows execute successfully
- [ ] Concurrent operations handled safely
- [ ] System remains stable under load
- [ ] Error recovery mechanisms work
- [ ] Performance degrades gracefully
- [ ] Resource cleanup occurs properly

---

## Expected Response Formats

### Success Response
```json
{
  "success": true,
  "data": {
    // Tool-specific response data
  },
  "message": "Operation completed successfully",
  "metadata": {
    "execution_time": "0.123s",
    "tool_version": "0.1.0",
    "timestamp": "2025-01-29T10:30:00Z"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid work_item_id format",
    "details": {
      "parameter": "work_item_id",
      "expected": "UUID, title, or keywords",
      "received": "invalid_format"
    }
  },
  "timestamp": "2025-01-29T10:30:00Z"
}
```

---

## Test Execution Instructions

### ⚠️ Before Starting: MCP Server Restart Reminder
**If ANY changes were made to the MCP server before testing, ensure the user has restarted the MCP server instance in their editor before proceeding.**

### Phase 1: Individual Tool Testing (Estimated: 4-6 hours)
1. Execute each tool test in category order
2. Validate all parameters and responses
3. Document any issues or unexpected behavior
4. Verify error handling for invalid inputs
5. **If tool fixes are needed**: Request user to restart MCP server before retesting

### Phase 2: Integration Testing (Estimated: 2-3 hours)
1. Run complete workflow scenarios
2. Test cross-tool interactions
3. Validate data consistency
4. Test concurrent operations

### Phase 3: Performance Testing (Estimated: 1-2 hours)
1. Execute load tests with multiple operations
2. Monitor system resource usage
3. Validate response times
4. Test system stability under stress

### Phase 4: Validation and Reporting (Estimated: 1 hour)
1. Compile test results
2. Document any failures or issues
3. Verify all 35 tools are functional
4. Generate comprehensive test report

---

## Success Criteria

### Tool-Level Success:
- ✅ All 35 tools execute without critical errors
- ✅ Parameter validation works correctly
- ✅ Response formats are consistent
- ✅ Error handling is comprehensive
- ✅ Performance meets requirements (< 5s per operation)

### Integration-Level Success:
- ✅ Complex workflows execute successfully
- ✅ Data consistency maintained across operations
- ✅ Concurrent operations handled safely
- ✅ System remains stable under load
- ✅ Error recovery mechanisms function properly

### Overall Success:
- ✅ 100% of tools pass individual tests
- ✅ All integration scenarios complete successfully
- ✅ Performance requirements met
- ✅ No critical bugs or data corruption
- ✅ System ready for production AI agent workflows

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Tool Not Found or Outdated Behavior
**Symptoms**: Tool returns "not found" error or exhibits old behavior after code changes
**Solution**: 
```
🔄 REQUEST USER TO RESTART MCP SERVER

The MCP server instance in your editor needs to be restarted to reflect recent changes.
Please restart the MCP server and try the test again.
```

#### Tool Count Mismatch
**Symptoms**: Less than 35 tools available in full mode
**Solution**: 
1. Verify `MCP_TOOL_MODE=full` environment variable
2. Request user to restart MCP server
3. Check server logs for initialization errors

#### Inconsistent Tool Responses
**Symptoms**: Same tool call returns different results
**Solution**:
1. Check for recent server code changes
2. Request user to restart MCP server if changes were made
3. Verify database state consistency

---

**Test Suite Version**: 1.0  
**Compatible with**: MCP Jive Full Mode (35 Tools)  
**Last Updated**: 2025-01-29  
**Estimated Execution Time**: 8-12 hours  
**Prerequisites**: MCP Jive server running in full mode with clean test environment

**⚠️ REMEMBER**: Always request user to restart MCP server after any code changes before testing!

This comprehensive test suite ensures that all 35 MCP tools are thoroughly validated for production use with AI agents in complex agile workflow scenarios.