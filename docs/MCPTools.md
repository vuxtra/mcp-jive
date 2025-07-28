# MCP Jive - Complete MCP Tools Reference

**Last Updated**: 2024-12-19  
**Status**: Compiled from PRD Analysis  
**Total Tools**: 47

## Overview

This document provides a comprehensive list of all MCP (Model Context Protocol) tools provided by the MCP Jive system across all components. Tools are organized by functional category and include purpose, description, and source PRD.

## Tool Categories

### 1. Hierarchy Management Tools
*Source: AGILE_WORKFLOW_ENGINE_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `create_work_item` | Work Item Creation | Create new work items in hierarchy (Initiative/Epic/Feature/Story/Task) |
| `update_work_item` | Work Item Modification | Modify existing work item properties, status, and relationships |
| `delete_work_item` | Work Item Removal | Remove work items and handle dependencies properly |
| `get_work_item_hierarchy` | Hierarchy Retrieval | Retrieve hierarchical structure of work items |
| `reorder_work_items` | Priority Management | Adjust work item priorities and ordering |

### 2. Dependency Management Tools
*Source: AGILE_WORKFLOW_ENGINE_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `add_dependency` | Dependency Creation | Create dependency relationships between work items |
| `remove_dependency` | Dependency Removal | Remove dependency links between work items |
| `validate_dependencies` | Dependency Validation | Check for circular dependencies and conflicts |
| `get_dependency_graph` | Dependency Visualization | Retrieve complete dependency structure |
| `calculate_critical_path` | Path Analysis | Identify critical execution path through dependencies |

### 3. Execution Control Tools
*Source: AGILE_WORKFLOW_ENGINE_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `execute_work_item` | Work Execution | Start autonomous execution of work item |
| `pause_execution` | Execution Control | Temporarily halt work item execution |
| `resume_execution` | Execution Control | Continue paused work item execution |
| `cancel_execution` | Execution Control | Stop and rollback work item execution |
| `get_execution_status` | Status Monitoring | Monitor real-time execution progress |

### 4. Progress Tracking Tools
*Source: AGILE_WORKFLOW_ENGINE_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `calculate_progress` | Progress Calculation | Compute completion percentages for work items |
| `get_milestone_status` | Milestone Tracking | Check milestone achievements and status |
| `update_work_item_status` | Status Updates | Modify work item completion status |
| `generate_progress_report` | Reporting | Create detailed progress summaries |

### 5. Task Management Tools
*Source: MCP_CLIENT_TOOLS_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `create_work_item` | Task Creation | Create new agile work items (Initiative/Epic/Feature/Story/Task) |
| `get_work_item` | Task Retrieval | Retrieve work item details by ID |
| `update_work_item` | Task Modification | Update work item properties, status, and relationships |
| `delete_work_item` | Task Removal | Delete work items with proper dependency handling |
| `list_work_items` | Task Listing | List work items with filtering and pagination |

### 6. Search and Discovery Tools
*Source: MCP_CLIENT_TOOLS_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `search_work_items` | Content Search | Semantic and keyword search across work items |
| `get_work_item_children` | Hierarchy Navigation | Retrieve child work items in hierarchy |
| `get_work_item_dependencies` | Dependency Discovery | Get dependency relationships for work items |
| `find_related_items` | Relationship Discovery | Find semantically related work items |
| `get_work_item_hierarchy` | Hierarchy Retrieval | Retrieve complete hierarchy tree |

### 7. Workflow Execution Tools
*Source: MCP_CLIENT_TOOLS_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `execute_work_item` | Work Execution | Start autonomous execution of work items |
| `get_execution_status` | Execution Monitoring | Monitor execution progress and status |
| `cancel_execution` | Execution Control | Cancel ongoing executions |
| `validate_completion` | Completion Validation | Validate work item completion |
| `trigger_dependent_execution` | Dependency Execution | Execute dependent work items |

### 8. Progress Tracking Tools (Client)
*Source: MCP_CLIENT_TOOLS_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `update_work_item_status` | Status Management | Update status and progress |
| `get_progress_summary` | Progress Reporting | Get progress metrics and summaries |
| `track_execution_metrics` | Metrics Tracking | Track performance and completion metrics |
| `generate_status_report` | Status Reporting | Generate progress reports |
| `sync_progress_data` | Data Synchronization | Synchronize progress with storage systems |

### 9. File System Management Tools
*Source: TASK_STORAGE_SYNC_SYSTEM_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `sync_file_to_database` | File Sync | Synchronize local file changes to Weaviate |
| `sync_database_to_file` | Database Sync | Update local files from database changes |
| `get_sync_status` | Sync Monitoring | Retrieve current synchronization status |
| `resolve_sync_conflict` | Conflict Resolution | Handle merge conflicts between file and database |
| `validate_file_format` | Format Validation | Check file format compliance |

### 10. Search and Discovery Tools (Storage)
*Source: TASK_STORAGE_SYNC_SYSTEM_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `search_work_items` | Vector Search | Semantic and keyword search across work items |
| `find_related_items` | Similarity Search | Discover related work items using vector similarity |
| `get_work_item_by_id` | Item Retrieval | Retrieve specific work item by identifier |
| `list_work_items_by_type` | Type Filtering | Filter work items by type (Epic, Feature, etc.) |
| `search_by_criteria` | Advanced Search | Advanced search with multiple filters |

### 11. Storage Management Tools
*Source: TASK_STORAGE_SYNC_SYSTEM_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `backup_local_storage` | Backup Management | Create backup of local .jivedev directory |
| `restore_from_backup` | Backup Restoration | Restore local storage from backup |
| `validate_storage_integrity` | Data Validation | Check data consistency between file and database |
| `optimize_vector_index` | Performance Optimization | Optimize Weaviate vector indexes |
| `cleanup_orphaned_files` | Cleanup Operations | Remove files without corresponding database entries |

### 12. Progress Tracking Tools (Service)
*Source: PROGRESS_TRACKING_DASHBOARD_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `get_progress` | Progress Retrieval | Retrieve progress metrics for tasks, features, epics, or initiatives |
| `get_completion_status` | Status Retrieval | Get detailed completion status with validation results |
| `calculate_velocity` | Velocity Calculation | Calculate team/agent velocity and productivity metrics |
| `get_critical_path` | Path Analysis | Analyze and return critical path dependencies |
| `get_bottlenecks` | Bottleneck Detection | Identify current bottlenecks and blocking issues |

### 13. Validation and Quality Tools
*Source: PROGRESS_TRACKING_DASHBOARD_PRD*

| Tool Name | Purpose | Description |
|-----------|---------|-------------|
| `validate_task_completion` | Completion Validation | Validate task completion against acceptance criteria |
| `run_quality_gates` | Quality Assurance | Execute quality gate checks for work items |
| `get_validation_status` | Validation Monitoring | Retrieve validation results and approval status |
| `approve_completion` | Approval Management | Mark work items as approved after validation |
| `request_changes` | Change Management | Request changes with specific feedback for work items |

## Analysis: Tool Overlaps and Redundancies

### 🔴 Critical Overlaps (Exact Duplicates)

The following tools appear multiple times across different PRDs with identical functionality:

#### 1. Work Item Management
- **`create_work_item`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD
- **`update_work_item`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD  
- **`delete_work_item`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD
- **`get_work_item_hierarchy`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD

#### 2. Execution Control
- **`execute_work_item`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD
- **`get_execution_status`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD
- **`cancel_execution`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD

#### 3. Progress Tracking
- **`update_work_item_status`**: Appears in AGILE_WORKFLOW_ENGINE_PRD and MCP_CLIENT_TOOLS_PRD

#### 4. Search and Discovery
- **`search_work_items`**: Appears in MCP_CLIENT_TOOLS_PRD and TASK_STORAGE_SYNC_SYSTEM_PRD
- **`find_related_items`**: Appears in MCP_CLIENT_TOOLS_PRD and TASK_STORAGE_SYNC_SYSTEM_PRD

### 🟡 Functional Overlaps (Similar Purpose)

These tools have similar purposes but may have different implementations:

#### 1. Validation Tools
- **`validate_completion`** (MCP_CLIENT_TOOLS_PRD) vs **`validate_task_completion`** (PROGRESS_TRACKING_DASHBOARD_PRD)
- **`run_quality_gates`** (PROGRESS_TRACKING_DASHBOARD_PRD) vs general validation in other PRDs

#### 2. Progress Reporting
- **`generate_progress_report`** (AGILE_WORKFLOW_ENGINE_PRD) vs **`generate_status_report`** (MCP_CLIENT_TOOLS_PRD)
- **`get_progress_summary`** (MCP_CLIENT_TOOLS_PRD) vs **`get_progress`** (PROGRESS_TRACKING_DASHBOARD_PRD)

#### 3. Work Item Retrieval
- **`get_work_item`** (MCP_CLIENT_TOOLS_PRD) vs **`get_work_item_by_id`** (TASK_STORAGE_SYNC_SYSTEM_PRD)
- **`list_work_items`** (MCP_CLIENT_TOOLS_PRD) vs **`list_work_items_by_type`** (TASK_STORAGE_SYNC_SYSTEM_PRD)

## Recommendations

### 🎯 Consolidation Strategy

1. **Merge Duplicate Tools**: Consolidate exact duplicates into single implementations
   - Keep core CRUD operations in MCP_CLIENT_TOOLS_PRD
   - Move execution control to AGILE_WORKFLOW_ENGINE_PRD
   - Centralize search in TASK_STORAGE_SYNC_SYSTEM_PRD

2. **Clarify Tool Boundaries**: 
   - **Engine Tools**: Core workflow logic and execution
   - **Client Tools**: User-facing operations and basic CRUD
   - **Storage Tools**: Data persistence and search
   - **Dashboard Tools**: Monitoring and reporting

3. **Reduce Tool Count**: From 47 tools to approximately 32 tools by eliminating duplicates

### 🔧 Specific Actions

1. **Remove from MCP_CLIENT_TOOLS_PRD**:
   - `execute_work_item`, `get_execution_status`, `cancel_execution` (move to Engine)
   - `search_work_items`, `find_related_items` (move to Storage)

2. **Remove from AGILE_WORKFLOW_ENGINE_PRD**:
   - `create_work_item`, `update_work_item`, `delete_work_item` (keep in Client)

3. **Standardize Naming**:
   - `validate_completion` → `validate_task_completion`
   - `get_work_item` → `get_work_item_by_id`
   - `generate_progress_report` → `generate_status_report`

### 📊 Final Tool Distribution

- **AGILE_WORKFLOW_ENGINE_PRD**: 15 tools (execution, dependencies, progress calculation)
- **MCP_CLIENT_TOOLS_PRD**: 8 tools (basic CRUD, status updates)
- **TASK_STORAGE_SYNC_SYSTEM_PRD**: 15 tools (storage, sync, search)
- **PROGRESS_TRACKING_DASHBOARD_PRD**: 10 tools (monitoring, validation, reporting)

**Total Optimized**: 32 tools (reduction of 15 duplicate/redundant tools)

This consolidation will improve maintainability, reduce confusion, and create clearer separation of concerns across the MCP Jive system.

---

## Refined Minimal MCP Tools for AI Agents

**Target**: 16 Essential Tools for Autonomous Coding

Based on the analysis above and the need for simple yet effective dependency and hierarchy tracking, here's the refined minimal tool set:

### 1. Core Work Item Management (5 tools)
| Tool | Purpose | AI Agent Use Case |
|------|---------|-------------------|
| `create_work_item` | Create coding tasks | "I need to create a new feature task" |
| `get_work_item` | Retrieve task details | "Show me what I need to build" |
| `update_work_item` | Update progress/status | "Mark this task as in progress" |
| `list_work_items` | Browse available tasks | "What tasks are available to work on?" |
| `search_work_items` | Find relevant tasks | "Find tasks related to authentication" |

### 2. Simple Hierarchy & Dependencies (3 tools)
| Tool | Purpose | AI Agent Use Case |
|------|---------|-------------------|
| `get_work_item_children` | Get child tasks | "What subtasks does this feature have?" |
| `get_work_item_dependencies` | Check what blocks this task | "What do I need to complete first?" |
| `validate_dependencies` | Ensure no circular deps | "Can I safely add this dependency?" |

### 3. Execution Control (3 tools)
| Tool | Purpose | AI Agent Use Case |
|------|---------|-------------------|
| `execute_work_item` | Start autonomous work | "Begin coding this task" |
| `get_execution_status` | Monitor progress | "How is my current task progressing?" |
| `cancel_execution` | Stop if needed | "Cancel this work and rollback" |

### 4. Storage & Sync (3 tools)
| Tool | Purpose | AI Agent Use Case |
|------|---------|-------------------|
| `sync_file_to_database` | Save task metadata and work item changes to database | "Persist my task progress and metadata" |
| `sync_database_to_file` | Load latest task data from database to .jivedev files | "Get the latest task assignments and status" |
| `get_sync_status` | Check synchronization state between files and database | "Are my task files synchronized with the database?" |

### 5. Validation (2 tools)
| Tool | Purpose | AI Agent Use Case |
|------|---------|-------------------|
| `validate_completion` | Check if work meets acceptance criteria and requirements | "Is my implementation complete and does it satisfy all requirements?" |
| `validate_file_format` | Ensure task metadata and .jivedev file format compliance | "Are my task files properly formatted and valid?" |

## Key Design Principles

### 🎯 Simplicity First
- **Linear Workflow**: Get Task → Check Dependencies → Execute → Validate → Save
- **Minimal Hierarchy**: Only parent-child relationships, no deep nesting
- **Essential Dependencies**: Only blocking relationships, no complex graphs

### 🔄 AI Agent Workflow
```
1. list_work_items() → Find available tasks
2. get_work_item(id) → Understand requirements
3. get_work_item_dependencies(id) → Check blockers
4. execute_work_item(id) → Start working on task
5. get_execution_status(id) → Monitor task progress
6. validate_completion(id) → Check if task meets acceptance criteria
7. sync_file_to_database() → Save task progress and metadata
```

### 🚀 Benefits for AI Agents
- **Focused**: Only tools needed for autonomous task management and execution
- **Predictable**: Clear workflow with minimal decision points
- **Safe**: Built-in validation and dependency checking
- **Efficient**: No complex reporting or dashboard overhead

### 📊 Comparison
- **Original**: 47 tools across 5 PRDs
- **Consolidated**: 32 tools (previous recommendation)
- **AI-Optimized**: 16 tools (this recommendation)

**Reduction**: 66% fewer tools while maintaining essential functionality for AI agents managing autonomous coding tasks and agile workflows.