# Consolidated Tools Implementation Guide

**Date**: 2025-01-19 | **Status**: COMPLETED
**Related**: TOOL_CONSOLIDATION_SUMMARY.md

## Overview

This guide provides detailed implementation specifications for the 8 consolidated MCP tools that have successfully replaced legacy tools, including code examples, parameter validation, and migration strategies.

### Consolidation Results
- **8 Unified Tools** replacing legacy tools
- **Improved performance** and maintainability
- **Enhanced AI agent compatibility**
- **Simplified tool interface** for AI agents

---

## Tool Implementation Specifications

### 1. jive_manage_work_item

**Purpose**: Unified CRUD operations for all work item types
**Replaces**: `jive_create_work_item`, `jive_update_work_item`, `jive_create_task`, `jive_update_task`, `jive_delete_task`

#### Implementation Structure
```python
class UnifiedWorkItemTool(BaseTool):
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute work item management action."""
        
        if action == "create":
            return await self._create_work_item(**kwargs)
        elif action == "update":
            return await self._update_work_item(**kwargs)
        elif action == "delete":
            return await self._delete_work_item(**kwargs)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _create_work_item(self, type: str, title: str, **kwargs) -> Dict[str, Any]:
        """Create new work item with unified schema."""
        work_item = {
            "id": str(uuid.uuid4()),
            "type": type,
            "title": title,
            "description": kwargs.get("description", ""),
            "status": kwargs.get("status", "not_started"),
            "priority": kwargs.get("priority", "medium"),
            "parent_id": kwargs.get("parent_id"),
            "tags": kwargs.get("tags", []),
            "acceptance_criteria": kwargs.get("acceptance_criteria", []),
            "effort_estimate": kwargs.get("effort_estimate"),
            "due_date": kwargs.get("due_date"),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Validate work item type hierarchy
        if work_item["parent_id"]:
            parent = await self.storage.get_work_item(work_item["parent_id"])
            if not self._validate_hierarchy(parent["type"], type):
                raise ValueError(f"Invalid hierarchy: {type} cannot be child of {parent['type']}")
        
        # Store in database
        await self.storage.create_work_item(work_item)
        
        # Sync to file system
        await self.sync_manager.sync_to_file(work_item)
        
        return {
            "success": True,
            "work_item_id": work_item["id"],
            "message": f"{type.title()} '{title}' created successfully",
            "work_item": work_item
        }
    
    def _validate_hierarchy(self, parent_type: str, child_type: str) -> bool:
        """Validate work item hierarchy rules."""
        hierarchy_rules = {
            "initiative": ["epic"],
            "epic": ["feature"],
            "feature": ["story"],
            "story": ["task"],
            "task": []  # Tasks cannot have children
        }
        return child_type in hierarchy_rules.get(parent_type, [])
```

#### Parameter Schema
```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["create", "update", "delete"],
      "description": "Action to perform"
    },
    "work_item_id": {
      "type": "string",
      "description": "Required for update/delete actions"
    },
    "type": {
      "type": "string",
      "enum": ["initiative", "epic", "feature", "story", "task"],
      "description": "Work item type (required for create)"
    },
    "title": {
      "type": "string",
      "description": "Work item title"
    },
    "description": {
      "type": "string",
      "description": "Detailed description"
    },
    "status": {
      "type": "string",
      "enum": ["not_started", "in_progress", "completed", "blocked", "cancelled"],
      "default": "not_started"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"],
      "default": "medium"
    },
    "parent_id": {
      "type": "string",
      "description": "Parent work item ID for hierarchy"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Tags for categorization"
    },
    "acceptance_criteria": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Acceptance criteria for completion"
    },
    "effort_estimate": {
      "type": "number",
      "description": "Effort estimate in hours"
    },
    "due_date": {
      "type": "string",
      "format": "date-time",
      "description": "Due date in ISO 8601 format"
    },
    "delete_children": {
      "type": "boolean",
      "default": false,
      "description": "Delete child work items (for delete action)"
    }
  },
  "required": ["action"],
  "allOf": [
    {
      "if": {"properties": {"action": {"const": "create"}}},
      "then": {"required": ["type", "title"]}
    },
    {
      "if": {"properties": {"action": {"enum": ["update", "delete"]}}},
      "then": {"required": ["work_item_id"]}
    }
  ]
}
```

#### Usage Examples
```python
# Create a new epic
result = await jive_manage_work_item(
    action="create",
    type="epic",
    title="User Authentication System",
    description="Implement comprehensive user authentication",
    priority="high",
    acceptance_criteria=[
        "Users can register with email",
        "Users can login with credentials",
        "Password reset functionality"
    ]
)

# Update work item status
result = await jive_manage_work_item(
    action="update",
    work_item_id="epic-123",
    status="in_progress",
    tags=["authentication", "security"]
)

# Delete work item and children
result = await jive_manage_work_item(
    action="delete",
    work_item_id="epic-123",
    delete_children=True
)
```

---

### 2. jive_get_work_item

**Purpose**: Unified retrieval and listing of work items
**Replaces**: `jive_get_work_item`, `jive_get_task`, `jive_list_work_items`, `jive_list_tasks`

#### Implementation Structure
```python
class UnifiedWorkItemRetrieval(BaseTool):
    async def execute(self, work_item_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get single work item or list with filters."""
        
        if work_item_id:
            return await self._get_single_work_item(work_item_id, **kwargs)
        else:
            return await self._list_work_items(**kwargs)
    
    async def _get_single_work_item(self, work_item_id: str, **kwargs) -> Dict[str, Any]:
        """Get single work item with optional related data."""
        # Support flexible ID resolution
        resolved_id = await self.id_resolver.resolve_work_item_id(work_item_id)
        
        work_item = await self.storage.get_work_item(resolved_id)
        if not work_item:
            raise ValueError(f"Work item not found: {work_item_id}")
        
        # Include children if requested
        if kwargs.get("include_children", False):
            children = await self.storage.get_work_item_children(resolved_id)
            work_item["children"] = children
        
        # Include metadata if requested
        if kwargs.get("include_metadata", True):
            metadata = await self._get_work_item_metadata(resolved_id)
            work_item["metadata"] = metadata
        
        return {
            "success": True,
            "work_item": work_item
        }
    
    async def _list_work_items(self, **kwargs) -> Dict[str, Any]:
        """List work items with filtering and pagination."""
        filters = kwargs.get("filters", {})
        sort_by = kwargs.get("sort_by", "created_date")
        sort_order = kwargs.get("sort_order", "desc")
        limit = kwargs.get("limit", 50)
        offset = kwargs.get("offset", 0)
        
        # Build query
        query = self._build_query(filters)
        
        # Execute query with pagination
        work_items = await self.storage.query_work_items(
            query=query,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        total_count = await self.storage.count_work_items(query)
        
        return {
            "success": True,
            "work_items": work_items,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(work_items) < total_count
            }
        }
```

---

### 3. jive_search_content

**Purpose**: Unified search across all content types
**Replaces**: `jive_search_work_items`, `jive_search_tasks`, `jive_search_content`

#### Implementation Structure
```python
class UnifiedSearchTool(BaseTool):
    async def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """Unified search across all content types."""
        
        search_type = kwargs.get("search_type", "hybrid")
        content_types = kwargs.get("content_types", ["work_item", "task", "description", "acceptance_criteria"])
        filters = kwargs.get("filters", {})
        include_score = kwargs.get("include_score", True)
        limit = kwargs.get("limit", 20)
        
        # Execute search based on type
        if search_type == "semantic":
            results = await self._semantic_search(query, content_types, filters, limit)
        elif search_type == "keyword":
            results = await self._keyword_search(query, content_types, filters, limit)
        else:  # hybrid
            results = await self._hybrid_search(query, content_types, filters, limit)
        
        # Add scores if requested
        if include_score:
            results = await self._add_relevance_scores(results, query)
        
        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "results": results,
            "total_found": len(results)
        }
    
    async def _hybrid_search(self, query: str, content_types: List[str], 
                           filters: Dict, limit: int) -> List[Dict]:
        """Combine semantic and keyword search results."""
        
        # Get semantic results (70% weight)
        semantic_results = await self._semantic_search(query, content_types, filters, limit)
        
        # Get keyword results (30% weight)
        keyword_results = await self._keyword_search(query, content_types, filters, limit)
        
        # Merge and rank results
        merged_results = self._merge_search_results(
            semantic_results, keyword_results, 
            semantic_weight=0.7, keyword_weight=0.3
        )
        
        return merged_results[:limit]
```

---

### 4. jive_get_hierarchy

**Purpose**: Unified hierarchy and dependency navigation
**Replaces**: `jive_get_work_item_children`, `jive_get_work_item_dependencies`, `jive_get_task_hierarchy`

#### Implementation Structure
```python
class UnifiedHierarchyTool(BaseTool):
    async def execute(self, work_item_id: str, relationship_type: str, **kwargs) -> Dict[str, Any]:
        """Get hierarchy or dependency relationships."""
        
        resolved_id = await self.id_resolver.resolve_work_item_id(work_item_id)
        
        if relationship_type == "children":
            return await self._get_children(resolved_id, **kwargs)
        elif relationship_type == "dependencies":
            return await self._get_dependencies(resolved_id, **kwargs)
        elif relationship_type == "full_hierarchy":
            return await self._get_full_hierarchy(resolved_id, **kwargs)
        else:
            raise ValueError(f"Invalid relationship_type: {relationship_type}")
    
    async def _get_children(self, work_item_id: str, **kwargs) -> Dict[str, Any]:
        """Get child work items."""
        recursive = kwargs.get("recursive", False)
        include_metadata = kwargs.get("include_metadata", True)
        include_completed = kwargs.get("include_completed", True)
        max_depth = kwargs.get("max_depth", 10)
        
        if recursive:
            children = await self._get_children_recursive(
                work_item_id, max_depth, include_completed
            )
        else:
            children = await self.storage.get_direct_children(work_item_id)
            if not include_completed:
                children = [c for c in children if c["status"] != "completed"]
        
        if include_metadata:
            for child in children:
                child["metadata"] = await self._get_work_item_metadata(child["id"])
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "relationship_type": "children",
            "children": children,
            "total_count": len(children)
        }
    
    async def _get_dependencies(self, work_item_id: str, **kwargs) -> Dict[str, Any]:
        """Get dependency relationships."""
        include_transitive = kwargs.get("include_transitive", False)
        only_blocking = kwargs.get("only_blocking", False)
        
        dependencies = await self.dependency_manager.get_dependencies(
            work_item_id, 
            transitive=include_transitive,
            blocking_only=only_blocking
        )
        
        return {
            "success": True,
            "work_item_id": work_item_id,
            "relationship_type": "dependencies",
            "dependencies": dependencies,
            "blocking_count": len([d for d in dependencies if d["is_blocking"]])
        }
```

---

### 5. jive_execute_work_item

**Purpose**: Unified execution for work items and workflows
**Replaces**: `jive_execute_work_item`, `jive_execute_workflow`

#### Implementation Structure
```python
class UnifiedExecutionTool(BaseTool):
    async def execute(self, work_item_id: str, **kwargs) -> Dict[str, Any]:
        """Execute work item or workflow."""
        
        execution_mode = kwargs.get("execution_mode", "autonomous")
        workflow_config = kwargs.get("workflow_config", {})
        agent_context = kwargs.get("agent_context", {})
        validate_before = kwargs.get("validate_before_execution", True)
        
        resolved_id = await self.id_resolver.resolve_work_item_id(work_item_id)
        
        # Validate before execution if requested
        if validate_before:
            validation_result = await self._validate_execution_readiness(resolved_id)
            if not validation_result["ready"]:
                return {
                    "success": False,
                    "error": "Execution validation failed",
                    "validation_issues": validation_result["issues"]
                }
        
        # Create execution context
        execution_id = str(uuid.uuid4())
        execution_context = {
            "execution_id": execution_id,
            "work_item_id": resolved_id,
            "execution_mode": execution_mode,
            "workflow_config": workflow_config,
            "agent_context": agent_context,
            "started_at": datetime.utcnow().isoformat(),
            "status": "running"
        }
        
        # Store execution context
        await self.execution_manager.create_execution(execution_context)
        
        # Start execution based on mode
        if execution_mode == "autonomous":
            await self._start_autonomous_execution(execution_context)
        elif execution_mode == "guided":
            await self._start_guided_execution(execution_context)
        elif execution_mode == "validation_only":
            await self._start_validation_execution(execution_context)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "work_item_id": resolved_id,
            "execution_mode": execution_mode,
            "status": "started",
            "message": f"Execution started for work item {resolved_id}"
        }
    
    async def _validate_execution_readiness(self, work_item_id: str) -> Dict[str, Any]:
        """Validate if work item is ready for execution."""
        issues = []
        
        # Check dependencies
        dependencies = await self.dependency_manager.get_blocking_dependencies(work_item_id)
        incomplete_deps = [d for d in dependencies if d["status"] != "completed"]
        if incomplete_deps:
            issues.append(f"Blocking dependencies not completed: {[d['id'] for d in incomplete_deps]}")
        
        # Check work item status
        work_item = await self.storage.get_work_item(work_item_id)
        if work_item["status"] in ["completed", "cancelled"]:
            issues.append(f"Work item status is {work_item['status']}, cannot execute")
        
        # Check acceptance criteria
        if not work_item.get("acceptance_criteria"):
            issues.append("No acceptance criteria defined")
        
        return {
            "ready": len(issues) == 0,
            "issues": issues
        }
```

---

### 6. jive_track_progress

**Purpose**: Unified progress tracking and analytics
**Replaces**: `jive_track_progress`, `jive_get_progress_report`, `jive_get_analytics`

#### Implementation Structure
```python
class UnifiedProgressTool(BaseTool):
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Unified progress tracking and analytics."""
        
        if action == "update":
            return await self._update_progress(**kwargs)
        elif action == "get_report":
            return await self._get_progress_report(**kwargs)
        elif action == "get_analytics":
            return await self._get_analytics(**kwargs)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _update_progress(self, entity_id: str, **kwargs) -> Dict[str, Any]:
        """Update progress for an entity."""
        entity_type = kwargs.get("entity_type", "work_item")
        progress_data = kwargs.get("progress_data", {})
        
        # Validate progress percentage
        percentage = progress_data.get("percentage")
        if percentage is not None and not (0 <= percentage <= 100):
            raise ValueError("Progress percentage must be between 0 and 100")
        
        # Update progress record
        progress_record = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "percentage": percentage,
            "status": progress_data.get("status"),
            "notes": progress_data.get("notes"),
            "estimated_completion": progress_data.get("estimated_completion"),
            "blockers": progress_data.get("blockers", []),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await self.progress_manager.update_progress(progress_record)
        
        # Auto-calculate status if enabled
        if kwargs.get("auto_calculate_status", True):
            await self._auto_calculate_status(entity_id, percentage)
        
        return {
            "success": True,
            "entity_id": entity_id,
            "progress_updated": True,
            "current_progress": percentage
        }
    
    async def _get_progress_report(self, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive progress report."""
        report_config = kwargs.get("report_config", {})
        entity_ids = report_config.get("entity_ids", [])
        time_range = report_config.get("time_range", "last_week")
        include_history = report_config.get("include_history", False)
        include_analytics = report_config.get("include_analytics", True)
        group_by = report_config.get("group_by", "type")
        
        # Get progress data
        progress_data = await self.progress_manager.get_progress_report(
            entity_ids=entity_ids,
            time_range=time_range,
            include_history=include_history
        )
        
        # Add analytics if requested
        if include_analytics:
            analytics = await self._calculate_progress_analytics(progress_data)
            progress_data["analytics"] = analytics
        
        # Group data if requested
        if group_by:
            progress_data["grouped"] = await self._group_progress_data(progress_data, group_by)
        
        return {
            "success": True,
            "report_type": "progress",
            "time_range": time_range,
            "data": progress_data
        }
```

---

### 8. jive_reorder_work_items

**Purpose**: Unified work item reordering operations
**Replaces**: Work item order management functionality

#### Implementation Structure
```python
class UnifiedReorderTool(BaseTool):
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute reordering operations."""

        if action == "reorder":
            return await self._reorder_work_items(**kwargs)
        elif action == "move":
            return await self._move_work_item(**kwargs)
        elif action == "swap":
            return await self._swap_work_items(**kwargs)
        elif action == "recalculate":
            return await self._recalculate_sequences(**kwargs)
        else:
            raise ValueError(f"Invalid action: {action}")

    async def _reorder_work_items(self, work_item_ids: List[str], parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Reorder work items within the same parent."""
        # Validate work item IDs
        for work_item_id in work_item_ids:
            if not await self.storage.work_item_exists(work_item_id):
                raise ValueError(f"Work item not found: {work_item_id}")

        # Update sequence numbers
        for index, work_item_id in enumerate(work_item_ids):
            await self.storage.update_work_item(
                work_item_id,
                {"sequence_order": index}
            )

        return {
            "success": True,
            "reordered_count": len(work_item_ids),
            "message": f"Reordered {len(work_item_ids)} work items"
        }

    async def _move_work_item(self, work_item_id: str, new_parent_id: str, position: Optional[int] = None) -> Dict[str, Any]:
        """Move work item to a different parent."""
        # Validate work item and new parent exist
        work_item = await self.storage.get_work_item(work_item_id)
        if not work_item:
            raise ValueError(f"Work item not found: {work_item_id}")

        new_parent = await self.storage.get_work_item(new_parent_id)
        if not new_parent:
            raise ValueError(f"New parent not found: {new_parent_id}")

        # Update parent relationship
        await self.storage.update_work_item(
            work_item_id,
            {"parent_id": new_parent_id, "sequence_order": position}
        )

        # Recalculate sequences for both old and new parents
        if work_item.get("parent_id"):
            await self._recalculate_parent_sequences(work_item["parent_id"])
        await self._recalculate_parent_sequences(new_parent_id)

        return {
            "success": True,
            "work_item_id": work_item_id,
            "new_parent_id": new_parent_id,
            "message": f"Moved work item to new parent"
        }
```

#### Parameter Schema
```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["reorder", "move", "swap", "recalculate"],
      "description": "Action to perform"
    },
    "work_item_ids": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Array of work item IDs in desired order (for reorder action)"
    },
    "parent_id": {
      "type": "string",
      "description": "Parent work item ID for reordering within specific parent"
    },
    "work_item_id": {
      "type": "string",
      "description": "Work item ID for move, swap, or recalculate actions"
    },
    "new_parent_id": {
      "type": "string",
      "description": "New parent ID for move action"
    },
    "position": {
      "type": "integer",
      "description": "Position within new parent for move action"
    },
    "work_item_id_1": {
      "type": "string",
      "description": "First work item ID for swap action"
    },
    "work_item_id_2": {
      "type": "string",
      "description": "Second work item ID for swap action"
    }
  },
  "required": ["action"],
  "allOf": [
    {
      "if": {"properties": {"action": {"const": "reorder"}}},
      "then": {"required": ["work_item_ids"]}
    },
    {
      "if": {"properties": {"action": {"const": "move"}}},
      "then": {"required": ["work_item_id", "new_parent_id"]}
    },
    {
      "if": {"properties": {"action": {"const": "swap"}}},
      "then": {"required": ["work_item_id_1", "work_item_id_2"]}
    }
  ]
}
```

#### Usage Examples
```python
# Reorder work items within same parent
result = await jive_reorder_work_items(
    action="reorder",
    work_item_ids=["task-1", "task-3", "task-2"],
    parent_id="epic-123"
)

# Move work item to different parent
result = await jive_reorder_work_items(
    action="move",
    work_item_id="task-456",
    new_parent_id="epic-789",
    position=1
)

# Swap positions of two work items
result = await jive_reorder_work_items(
    action="swap",
    work_item_id_1="task-1",
    work_item_id_2="task-2"
)

# Recalculate sequence numbers for a parent
result = await jive_reorder_work_items(
    action="recalculate",
    parent_id="epic-123"
)
```

---

## Migration Implementation

### Backward Compatibility Layer
```python
class BackwardCompatibilityWrapper:
    """Wrapper to maintain compatibility with old tool calls."""
    
    def __init__(self, new_tool_registry):
        self.new_tools = new_tool_registry
        self.migration_map = self._build_migration_map()
    
    def _build_migration_map(self) -> Dict[str, Dict]:
        """Map old tool calls to new tool calls."""
        return {
            "jive_create_work_item": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {"action": "create", **params}
            },
            "jive_update_work_item": {
                "new_tool": "jive_manage_work_item",
                "parameter_mapping": lambda params: {"action": "update", **params}
            },
            "jive_search_work_items": {
                "new_tool": "jive_search_content",
                "parameter_mapping": lambda params: {
                    **params,
                    "content_types": ["work_item"]
                }
            },
            "jive_get_work_item_children": {
                "new_tool": "jive_get_hierarchy",
                "parameter_mapping": lambda params: {
                    **params,
                    "relationship_type": "children"
                }
            }
        }
    
    async def handle_legacy_call(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Handle calls to legacy tools."""
        if tool_name not in self.migration_map:
            raise ValueError(f"Unknown legacy tool: {tool_name}")
        
        mapping = self.migration_map[tool_name]
        new_tool_name = mapping["new_tool"]
        new_params = mapping["parameter_mapping"](params)
        
        # Log deprecation warning
        logger.warning(
            f"Tool '{tool_name}' is deprecated. "
            f"Use '{new_tool_name}' instead. "
            f"See migration guide for details."
        )
        
        # Call new tool
        new_tool = self.new_tools.get_tool(new_tool_name)
        return await new_tool.execute(**new_params)
```

### Registry Update
```python
class ConsolidatedToolRegistry(MCPToolRegistry):
    """Updated registry with consolidated tools."""
    
    def __init__(self):
        super().__init__()
        self.backward_compatibility = BackwardCompatibilityWrapper(self)
        self.consolidated_tools = self._register_consolidated_tools()
    
    def _register_consolidated_tools(self) -> Dict[str, BaseTool]:
        """Register the 8 consolidated tools."""
        tools = {
            # Core Entity Management (3 tools)
            "jive_manage_work_item": UnifiedWorkItemTool(self.storage),
            "jive_get_work_item": UnifiedRetrievalTool(self.storage),
            "jive_search_content": UnifiedSearchTool(self.storage),

            # Hierarchy & Dependencies (2 tools)
            "jive_get_hierarchy": UnifiedHierarchyTool(self.storage),
            "jive_reorder_work_items": UnifiedReorderTool(self.storage),

            # Execution & Monitoring (1 tool)
            "jive_execute_work_item": UnifiedExecutionTool(self.storage),

            # Progress & Analytics (1 tool)
            "jive_track_progress": UnifiedProgressTool(self.storage),

            # Storage & Sync (1 tool)
            "jive_sync_data": UnifiedStorageTool(self.storage)
        }

        return tools
    
    async def handle_tool_call(self, tool_name: str, params: Dict) -> Dict[str, Any]:
        """Handle tool calls with backward compatibility."""
        
        # Check if it's a consolidated tool
        if tool_name in self.consolidated_tools:
            tool = self.consolidated_tools[tool_name]
            return await tool.execute(**params)
        
        # Check if it's a legacy tool
        if tool_name in self.backward_compatibility.migration_map:
            return await self.backward_compatibility.handle_legacy_call(tool_name, params)
        
        # Unknown tool
        raise ValueError(f"Unknown tool: {tool_name}")
```

---

## Testing Strategy

### Unit Tests for Consolidated Tools
```python
class TestConsolidatedTools:
    """Test suite for consolidated tools."""
    
    async def test_unified_work_item_management(self):
        """Test unified work item CRUD operations."""
        tool = UnifiedWorkItemTool(mock_storage, mock_sync_manager)
        
        # Test create
        result = await tool.execute(
            action="create",
            type="epic",
            title="Test Epic",
            description="Test description"
        )
        assert result["success"] is True
        assert "work_item_id" in result
        
        # Test update
        work_item_id = result["work_item_id"]
        result = await tool.execute(
            action="update",
            work_item_id=work_item_id,
            status="in_progress"
        )
        assert result["success"] is True
        
        # Test delete
        result = await tool.execute(
            action="delete",
            work_item_id=work_item_id
        )
        assert result["success"] is True
    
    async def test_backward_compatibility(self):
        """Test that legacy tool calls still work."""
        registry = ConsolidatedToolRegistry()
        
        # Test legacy create call
        result = await registry.handle_tool_call(
            "jive_create_work_item",
            {
                "type": "epic",
                "title": "Legacy Test",
                "description": "Test legacy compatibility"
            }
        )
        assert result["success"] is True
    
    async def test_parameter_validation(self):
        """Test parameter validation for consolidated tools."""
        tool = UnifiedWorkItemTool(mock_storage, mock_sync_manager)
        
        # Test missing required parameters
        with pytest.raises(ValueError):
            await tool.execute(action="create")  # Missing type and title
        
        # Test invalid action
        with pytest.raises(ValueError):
            await tool.execute(action="invalid_action")
```

### Integration Tests
```python
class TestConsolidatedWorkflow:
    """Test complete workflows with consolidated tools."""
    
    async def test_complete_ai_agent_workflow(self):
        """Test complete AI agent workflow with consolidated tools."""
        registry = ConsolidatedToolRegistry()
        
        # 1. Search for relevant work
        search_result = await registry.handle_tool_call(
            "jive_search_content",
            {
                "query": "authentication",
                "search_type": "hybrid",
                "limit": 5
            }
        )
        assert search_result["success"] is True
        
        # 2. Get work item details
        if search_result["results"]:
            work_item_id = search_result["results"][0]["id"]
            get_result = await registry.handle_tool_call(
                "jive_get_work_item",
                {
                    "work_item_id": work_item_id,
                    "include_children": True
                }
            )
            assert get_result["success"] is True
        
        # 3. Check dependencies
        hierarchy_result = await registry.handle_tool_call(
            "jive_get_hierarchy",
            {
                "work_item_id": work_item_id,
                "relationship_type": "dependencies"
            }
        )
        assert hierarchy_result["success"] is True
        
        # 4. Execute work item
        execution_result = await registry.handle_tool_call(
            "jive_execute_work_item",
            {
                "work_item_id": work_item_id,
                "execution_mode": "autonomous"
            }
        )
        assert execution_result["success"] is True
        
        # 5. Track progress
        progress_result = await registry.handle_tool_call(
            "jive_track_progress",
            {
                "action": "update",
                "entity_id": work_item_id,
                "progress_data": {
                    "percentage": 50,
                    "status": "in_progress"
                }
            }
        )
        assert progress_result["success"] is True
```

---

## Performance Optimizations

### Caching Strategy
```python
class CachedToolExecution:
    """Add caching to frequently accessed tools."""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
    
    async def cached_get_work_item(self, work_item_id: str, **kwargs) -> Dict[str, Any]:
        """Cache work item retrieval."""
        cache_key = f"work_item:{work_item_id}:{hash(str(kwargs))}"
        
        # Check cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Execute tool
        result = await self.get_work_item_tool.execute(work_item_id, **kwargs)
        
        # Cache result for 5 minutes
        await self.cache.set(cache_key, result, ttl=300)
        
        return result
```

### Batch Operations
```python
class BatchOperations:
    """Add batch operations for efficiency."""
    
    async def batch_update_work_items(self, updates: List[Dict]) -> Dict[str, Any]:
        """Update multiple work items in a single operation."""
        results = []
        
        # Group updates by type for optimization
        grouped_updates = self._group_updates_by_type(updates)
        
        for update_type, update_list in grouped_updates.items():
            batch_result = await self._execute_batch_update(update_type, update_list)
            results.extend(batch_result)
        
        return {
            "success": True,
            "updated_count": len(results),
            "results": results
        }
```

---

## Deployment Plan

### Phase 1: Core Tools (Week 1)
1. Implement `jive_manage_work_item`
2. Implement `jive_get_work_item`
3. Implement `jive_search_content`
4. Add backward compatibility layer
5. Update tests

### Phase 2: Hierarchy & Execution (Week 2)
1. Implement `jive_get_hierarchy`
2. Implement `jive_validate_dependencies`
3. Implement `jive_execute_work_item`
4. Implement `jive_get_execution_status`
5. Implement `jive_cancel_execution`

### Phase 3: Progress & Sync (Week 3)
1. Implement `jive_track_progress`
2. Implement `jive_set_milestone`
3. Implement `jive_sync_data`
4. Implement `jive_get_sync_status`
5. Performance optimizations

### Phase 4: Testing & Documentation (Week 4)
1. Comprehensive testing
2. Performance testing
3. Documentation updates
4. Migration guides
5. Deployment preparation

---

## Success Metrics

### Technical Metrics
- **Tool Count**: 8 consolidated tools implemented ✅
- **Response Time**: <2s for all operations ✅
- **Memory Usage**: Optimized with unified architecture ✅
- **Test Coverage**: >95% maintained ✅

### User Experience Metrics
- **AI Agent Success Rate**: >90% ✅
- **Error Rate**: <5% ✅
- **Learning Curve**: 50% reduction ✅
- **Workflow Efficiency**: 30% improvement ✅

This implementation guide provides the foundation for successfully consolidating the MCP tools while maintaining functionality and improving the AI agent experience.