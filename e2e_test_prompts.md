# MCP Jive End-to-End Test Prompts

This document contains a comprehensive series of test prompts to validate MCP Jive functionality end-to-end. Execute these prompts in sequence to test the complete workflow.

## Prerequisites
- MCP Jive server running with MCP client integration
- At least one AI provider API key configured
- Clean database state (or note existing data)

---

## Phase 1: Basic Work Item Management

### Test 1.1: Create Initiative
**Prompt:**
```
Create a new initiative called "E-commerce Platform Modernization" with the description "Modernize our legacy e-commerce platform to improve performance, scalability, and user experience. This initiative will involve migrating to microservices architecture, implementing modern UI/UX, and enhancing security."
```

**Expected Result:** Initiative created with unique ID, proper hierarchy level

### Test 1.2: Create Epic Under Initiative
**Prompt:**
```
Create an epic called "User Authentication System" under the "E-commerce Platform Modernization" initiative. Description: "Implement secure, scalable user authentication with multi-factor authentication, social login, and role-based access control."
```

**Expected Result:** Epic created and linked to parent initiative

### Test 1.3: Create Features Under Epic
**Prompt:**
```
Create three features under the "User Authentication System" epic:
1. "Multi-Factor Authentication" - Implement SMS and email-based 2FA
2. "Social Login Integration" - Add Google, Facebook, and GitHub OAuth
3. "Role-Based Access Control" - Implement user roles and permissions
```

**Expected Result:** Three features created with proper parent-child relationships

### Test 1.4: Create Stories Under Features
**Prompt:**
```
For the "Multi-Factor Authentication" feature, create these user stories:
1. "As a user, I want to enable 2FA via SMS so that my account is more secure"
2. "As a user, I want to enable 2FA via email so that I have backup authentication"
3. "As an admin, I want to enforce 2FA for all users so that security is maintained"
```

**Expected Result:** User stories created with acceptance criteria

### Test 1.5: Create Tasks Under Stories
**Prompt:**
```
For the story "As a user, I want to enable 2FA via SMS", create these technical tasks:
1. "Set up SMS service integration (Twilio)"
2. "Create 2FA setup UI components"
3. "Implement SMS verification logic"
4. "Add 2FA database schema"
5. "Write unit tests for SMS 2FA"
```

**Expected Result:** Technical tasks created with effort estimates

---

## Phase 2: Work Item Queries and Management

### Test 2.1: Retrieve Work Item Details
**Prompt:**
```
Show me the complete details of the "E-commerce Platform Modernization" initiative including all its children and their current status.
```

**Expected Result:** Full hierarchy display with status information

### Test 2.2: Search Work Items
**Prompt:**
```
Search for all work items related to "authentication" and "security" across the entire project.
```

**Expected Result:** Semantic search results showing relevant items

### Test 2.3: List Work Items by Status
**Prompt:**
```
List all work items that are currently "not_started" and have high priority.
```

**Expected Result:** Filtered list of high-priority, not-started items

### Test 2.4: Update Work Item Status
**Prompt:**
```
Mark the "Set up SMS service integration (Twilio)" task as "in_progress" and update its effort estimate to 8 hours.
```

**Expected Result:** Task status and estimate updated successfully

---

## Phase 3: Dependencies and Relationships

### Test 3.1: Add Dependencies
**Prompt:**
```
Set up these dependencies:
- "Create 2FA setup UI components" depends on "Add 2FA database schema"
- "Implement SMS verification logic" depends on "Set up SMS service integration (Twilio)"
- "Write unit tests for SMS 2FA" depends on "Implement SMS verification logic"
```

**Expected Result:** Dependencies created and validated

### Test 3.2: Validate Dependencies
**Prompt:**
```
Validate the dependency graph for the entire "Multi-Factor Authentication" feature to check for circular dependencies and consistency issues.
```

**Expected Result:** Dependency validation report with any issues identified

### Test 3.3: Get Work Item Dependencies
**Prompt:**
```
Show me all dependencies that are blocking the "Write unit tests for SMS 2FA" task from being executed.
```

**Expected Result:** List of blocking dependencies with their current status

### Test 3.4: Get Work Item Children
**Prompt:**
```
Get all child work items for the "User Authentication System" epic, including their effort estimates and acceptance criteria.
```

**Expected Result:** Complete child hierarchy with metadata

---

## Phase 4: Workflow Execution and Monitoring

### Test 4.1: Execute Work Item
**Prompt:**
```
Start autonomous execution of the "Set up SMS service integration (Twilio)" task using dependency-based execution mode.
```

**Expected Result:** Execution started with unique execution ID

### Test 4.2: Monitor Execution Status
**Prompt:**
```
Check the execution status of the SMS service integration task, including logs and any generated artifacts.
```

**Expected Result:** Real-time execution progress and status information

### Test 4.3: Execute Feature-Level Work
**Prompt:**
```
Execute the entire "Multi-Factor Authentication" feature using parallel execution mode for independent tasks.
```

**Expected Result:** Feature-level execution with parallel task coordination

### Test 4.4: Cancel Execution
**Prompt:**
```
Cancel the execution of the "Multi-Factor Authentication" feature with rollback of any changes made during execution.
```

**Expected Result:** Execution cancelled and changes rolled back

---

## Phase 5: Validation and Approval

### Test 5.1: Validate Task Completion
**Prompt:**
```
Validate the completion of the "Add 2FA database schema" task against its acceptance criteria and code review standards.
```

**Expected Result:** Validation report with pass/fail status for each criterion

### Test 5.2: Custom Validation Checks
**Prompt:**
```
Perform custom validation on the "Create 2FA setup UI components" task with these checks:
1. UI components follow design system guidelines
2. Components are accessible (WCAG 2.1 AA compliant)
3. Components have proper error handling
4. Components include unit tests with >90% coverage
```

**Expected Result:** Custom validation results for each specified check

### Test 5.3: Approve Work Item
**Prompt:**
```
Approve the completion of the "Set up SMS service integration (Twilio)" task with full approval and automatic progression to the next workflow step.
```

**Expected Result:** Task approved and workflow progressed

### Test 5.4: Conditional Approval
**Prompt:**
```
Give conditional approval to the "Implement SMS verification logic" task with these conditions:
1. Security review must be completed within 48 hours
2. Performance testing must show <200ms response time
3. Error handling must be documented
```

**Expected Result:** Conditional approval with specified conditions tracked

---

## Phase 6: Data Synchronization

### Test 6.1: Sync File to Database
**Prompt:**
```
Sync a local task file containing updated metadata for the "Social Login Integration" feature to the vector database using auto-merge strategy.
```

**Expected Result:** File synchronized with conflict resolution applied

### Test 6.2: Sync Database to File
**Prompt:**
```
Sync the "Role-Based Access Control" feature from the database to a local YAML file with backup creation enabled.
```

**Expected Result:** Database content exported to file with backup created

### Test 6.3: Check Sync Status
**Prompt:**
```
Check the synchronization status of all tracked files, including any conflicts that need manual resolution.
```

**Expected Result:** Comprehensive sync status report with conflict details

### Test 6.4: Resolve Sync Conflicts
**Prompt:**
```
Resolve any synchronization conflicts for the "User Authentication System" epic using manual resolution strategy, prioritizing database content.
```

**Expected Result:** Conflicts resolved with chosen strategy applied

---

## Phase 7: Advanced Queries and Analytics

### Test 7.1: Complex Search Query
**Prompt:**
```
Find all high-priority tasks that are blocked by dependencies, have effort estimates greater than 4 hours, and are tagged with "security" or "authentication".
```

**Expected Result:** Complex filtered search results

### Test 7.2: Hierarchy Analysis
**Prompt:**
```
Analyze the complete work breakdown structure for the "E-commerce Platform Modernization" initiative, showing progress percentages at each level.
```

**Expected Result:** Hierarchical progress analysis with rollup calculations

### Test 7.3: Dependency Impact Analysis
**Prompt:**
```
Analyze the impact of delaying the "Set up SMS service integration (Twilio)" task by 1 week on the overall project timeline.
```

**Expected Result:** Impact analysis showing affected downstream work

### Test 7.4: Resource Allocation Query
**Prompt:**
```
Show me all work items assigned to team members, grouped by assignee, with total effort estimates and current workload.
```

**Expected Result:** Resource allocation summary with workload analysis

---

## Phase 8: Error Handling and Edge Cases

### Test 8.1: Invalid Work Item Creation
**Prompt:**
```
Try to create a task with an invalid parent ID and missing required fields to test error handling.
```

**Expected Result:** Appropriate error messages with validation details

### Test 8.2: Circular Dependency Detection
**Prompt:**
```
Attempt to create a circular dependency where Task A depends on Task B, Task B depends on Task C, and Task C depends on Task A.
```

**Expected Result:** Circular dependency detected and prevented

### Test 8.3: Concurrent Modification Handling
**Prompt:**
```
Simulate concurrent updates to the same work item to test conflict resolution mechanisms.
```

**Expected Result:** Concurrent modification handled gracefully

### Test 8.4: Large Dataset Performance
**Prompt:**
```
Create 100 work items in a batch and then perform complex queries to test performance with larger datasets.
```

**Expected Result:** Acceptable performance maintained with larger data volumes

---

## Phase 9: Integration and Workflow Testing

### Test 9.1: End-to-End Workflow
**Prompt:**
```
Execute a complete workflow from initiative creation through task completion, validation, and approval for a small feature.
```

**Expected Result:** Complete workflow executed successfully

### Test 9.2: Multi-Team Coordination
**Prompt:**
```
Create work items for multiple teams (Frontend, Backend, DevOps) with cross-team dependencies and coordinate their execution.
```

**Expected Result:** Multi-team coordination handled properly

### Test 9.3: Rollback and Recovery
**Prompt:**
```
Test rollback capabilities by starting execution, making partial progress, then rolling back to a previous state.
```

**Expected Result:** Rollback executed successfully with state restored

### Test 9.4: Notification and Reporting
**Prompt:**
```
Generate status reports and notifications for stakeholders based on current project progress and blockers.
```

**Expected Result:** Comprehensive reports generated with stakeholder notifications

---

## Validation Checklist

After completing all test phases, verify:

- [ ] All work item types (Initiative, Epic, Feature, Story, Task) can be created
- [ ] Hierarchical relationships are maintained correctly
- [ ] Dependencies are enforced and validated
- [ ] Search and filtering work across all data
- [ ] Workflow execution handles various scenarios
- [ ] Validation and approval processes function properly
- [ ] Data synchronization maintains consistency
- [ ] Error handling provides meaningful feedback
- [ ] Performance is acceptable under load
- [ ] Integration points work seamlessly

## Performance Benchmarks

- Work item creation: < 500ms
- Complex searches: < 2 seconds
- Dependency validation: < 1 second
- Workflow execution startup: < 3 seconds
- Data synchronization: < 1 second per file

## Expected Data State After Testing

After completing all tests, the system should contain:
- 1 Initiative
- 1 Epic
- 3 Features
- 3+ User Stories
- 5+ Technical Tasks
- Multiple dependencies between items
- Various status states across work items
- Execution history and validation records
- Synchronized file artifacts

This comprehensive test suite validates the complete MCP Jive functionality and ensures all components work together seamlessly.