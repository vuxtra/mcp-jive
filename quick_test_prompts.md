# MCP Jive Quick Test Suite

A condensed set of test prompts for rapid end-to-end validation of MCP Jive functionality.

## Quick Test Sequence (15 minutes)

### 1. Basic Work Item Creation
```
Create an initiative called "Mobile App Development" with description "Develop a new mobile application for our e-commerce platform with iOS and Android support."
```

### 2. Hierarchy Building
```
Create an epic called "User Authentication" under the Mobile App Development initiative, then create a feature called "Login System" under that epic, and finally create a task called "Implement OAuth integration" under the Login System feature.
```

### 3. Work Item Retrieval
```
Show me the complete hierarchy and details for the Mobile App Development initiative including all children.
```

### 4. Search Functionality
```
Search for all work items containing "authentication" or "login" keywords.
```

### 5. Dependency Management
```
Create a second task called "Design login UI" and make the "Implement OAuth integration" task depend on it.
```

### 6. Status Updates
```
Update the "Design login UI" task status to "in_progress" and set its effort estimate to 6 hours.
```

### 7. Dependency Validation
```
Validate the dependency graph for the Login System feature to check for any issues.
```

### 8. Work Item Execution
```
Start autonomous execution of the "Design login UI" task.
```

### 9. Execution Monitoring
```
Check the execution status of the "Design login UI" task including any logs or artifacts.
```

### 10. Task Completion Validation
```
Validate the completion of the "Design login UI" task against acceptance criteria and mark it as completed if validation passes.
```

## Expected Results Summary

✅ **Work Item Management**: Initiative → Epic → Feature → Task hierarchy created
✅ **Search & Retrieval**: Semantic search finds relevant items
✅ **Dependencies**: Tasks properly linked with dependency validation
✅ **Status Tracking**: Work items can be updated and tracked
✅ **Workflow Execution**: Tasks can be executed autonomously
✅ **Monitoring**: Real-time execution status available
✅ **Validation**: Completion criteria can be checked and enforced

## Success Criteria

- All 10 prompts execute without errors
- Work item hierarchy is properly maintained
- Dependencies are enforced correctly
- Search returns relevant results
- Execution can be started and monitored
- Validation provides meaningful feedback

## Troubleshooting

If any test fails:
1. Check MCP Jive server logs
2. Verify API keys are configured
3. Ensure database is accessible
4. Check tool mode configuration (minimal vs full)
5. Restart server if needed

This quick test suite validates core functionality in under 15 minutes.