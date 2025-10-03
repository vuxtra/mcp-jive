# MCP Jive Tool-Specific Test Prompts

Direct test prompts for individual MCP tools to validate each tool's functionality.

## Core Work Item Management Tools

### jive_create_work_item
```
Use the jive_create_work_item tool to create:
1. An initiative titled "Digital Transformation" with description "Company-wide digital transformation initiative"
2. An epic titled "Customer Portal" under the Digital Transformation initiative
3. A feature titled "User Dashboard" under the Customer Portal epic
4. A story titled "As a customer, I want to view my order history"
5. A task titled "Create order history API endpoint"
```

### jive_get_work_item
```
Use jive_get_work_item to retrieve the complete details of the Digital Transformation initiative, including all children and dependencies.
```

### jive_update_work_item
```
Use jive_update_work_item to:
1. Change the Customer Portal epic status to "in_progress"
2. Update the User Dashboard feature priority to "high"
3. Add acceptance criteria to the order history story
4. Set effort estimate of 8 hours for the API endpoint task
```

### jive_list_work_items
```
Use jive_list_work_items to:
1. List all work items with status "not_started"
2. List all high-priority work items
3. List all tasks with effort estimates > 5 hours
4. List work items created in the last 24 hours
```

### jive_search_work_items
```
Use jive_search_work_items to:
1. Search for "customer portal dashboard" using semantic search
2. Search for "API endpoint" using keyword search
3. Search for "order history" using hybrid search
4. Search with filters for only "feature" type items
```

## Hierarchy and Dependencies Tools

### jive_get_work_item_children
```
Use jive_get_work_item_children to:
1. Get all direct children of the Digital Transformation initiative
2. Get all descendants (recursive) of the Customer Portal epic
3. Get children with metadata including effort estimates
4. Get children without metadata for quick overview
```

### jive_get_work_item_dependencies
```
Use jive_get_work_item_dependencies to:
1. Check dependencies for the API endpoint task
2. Get transitive dependencies for the User Dashboard feature
3. Get only blocking dependencies for the order history story
4. Get all dependencies including non-blocking ones
```

### jive_validate_dependencies
```
Use jive_validate_dependencies to:
1. Validate the entire dependency graph for circular dependencies
2. Check for missing dependency references
3. Validate specific work items only
4. Get suggested fixes for any dependency issues
```

## Workflow Execution Tools

### jive_execute_work_item
```
Use jive_execute_work_item to:
1. Execute the API endpoint task using sequential mode
2. Execute the User Dashboard feature using parallel mode
3. Execute the Customer Portal epic using dependency-based mode
4. Execute with custom agent context and constraints
```

### jive_get_execution_status
```
Use jive_get_execution_status to:
1. Monitor the API endpoint task execution with logs
2. Check User Dashboard feature execution with artifacts
3. Get execution status with validation results
4. Monitor without logs for quick status check
```

### jive_cancel_execution
```
Use jive_cancel_execution to:
1. Cancel the Customer Portal epic execution with rollback
2. Force cancel an execution even if rollback fails
3. Cancel with a specific reason documented
4. Cancel without rollback for testing
```

## Validation and Approval Tools

### jive_validate_task_completion
```
Use jive_validate_task_completion to:
1. Validate the API endpoint task against acceptance criteria
2. Perform code review validation on the User Dashboard feature
3. Run security validation on the Customer Portal epic
4. Custom validation with specific checks:
   - Code coverage > 80%
   - Performance tests pass
   - Documentation complete
   - Security scan clean
```

### jive_approve_completion
```
Use jive_approve_completion to:
1. Give full approval to the API endpoint task
2. Give conditional approval to User Dashboard with conditions:
   - UI review must be completed
   - Accessibility testing required
3. Give partial approval with specific notes
4. Approve with expiration date set to 7 days
```

## Data Synchronization Tools

### jive_sync_file_to_database
```
Use jive_sync_file_to_database to:
1. Sync a task file using auto_merge strategy
2. Sync with file_wins strategy for local changes
3. Sync with database_wins for server priority
4. Validate only without actually syncing
```

### jive_sync_database_to_file
```
Use jive_sync_database_to_file to:
1. Export the Customer Portal epic to JSON format
2. Export the User Dashboard feature to YAML format
3. Sync with backup creation enabled
4. Use manual_resolution for conflicts
```

### jive_get_sync_status
```
Use jive_get_sync_status to:
1. Check sync status for a specific file
2. Check status for a specific work item ID
3. Include detailed conflict information
4. Check all tracked files at once
```

## Advanced Testing Scenarios

### Error Handling Tests
```
1. Try to create a work item with invalid parent ID
2. Attempt to update a non-existent work item
3. Search with malformed query parameters
4. Execute a work item that doesn't exist
5. Validate completion of incomplete work
6. Sync a file that doesn't exist
```

### Performance Tests
```
1. Create 50 work items in rapid succession
2. Search across large dataset with complex filters
3. Execute multiple work items simultaneously
4. Validate dependencies on large hierarchy
5. Sync multiple files concurrently
```

### Integration Tests
```
1. Create work item → Add dependencies → Execute → Validate → Approve (full workflow)
2. Create hierarchy → Search → Update → Sync to file → Sync back to database
3. Execute with cancellation → Rollback → Re-execute → Complete
4. Multi-user scenario with concurrent operations
```

## Tool Mode Specific Tests

### Minimal Mode (16 tools)
```
Test that only essential tools are available:
- Core work item CRUD operations
- Basic hierarchy management
- Simple execution and validation
- Basic synchronization
```

### Full Mode (47 tools)
```
Test additional tools available in full mode:
- Advanced analytics and reporting
- Complex workflow orchestration
- Detailed validation options
- Enhanced synchronization features
```

## Validation Checklist

For each tool test:
- [ ] Tool executes without errors
- [ ] Parameters are validated correctly
- [ ] Response format matches expected schema
- [ ] Error handling provides meaningful messages
- [ ] Performance is within acceptable limits
- [ ] Side effects are properly managed
- [ ] Data consistency is maintained

## Expected Tool Responses

### Success Response Format
```json
{
  "success": true,
  "data": { /* tool-specific data */ },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-XX..."
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* additional error context */ }
  },
  "timestamp": "2024-01-XX..."
}
```

This tool-specific test suite ensures each MCP tool functions correctly in isolation and integration scenarios.