# AI Agent Instructions: Using MCP Jive for Codebase Development

## Overview

MCP Jive provides hierarchical work management (Initiative → Epic → Feature → Story → Task) and knowledge management (Architecture & Troubleshooting Memory). Use these tools to plan systematically, document learnings, and track progress.

**When to use MCP Jive:**
- Complex features requiring multi-step implementation
- Building new codebases or major refactors
- Documenting architectural patterns for reuse
- Solving problems that may recur
- Managing dependencies between work items

**When NOT to use:**
- Simple bug fixes or one-line changes
- Exploratory coding or prototyping
- Tasks you can complete in under 30 minutes

## Strategic Workflow

### Phase 1: Planning & Discovery

**ALWAYS start by searching before creating:**

1. **Search for existing work** - Check if someone already planned or implemented similar functionality
   - Use `jive_search_content` with semantic search for natural language queries
   - Filter by status to see completed work for reference
   - Check hierarchy to understand existing structure

2. **Search for architectural patterns** - Look for established patterns before designing
   - Use `jive_memory` with `action: "search"` and `memory_type: "architecture"`
   - Review related patterns using `children_slugs` and `related_slugs`
   - Check `linked_epic_ids` to see where patterns were applied

3. **Search for known solutions** - Check if the problem was solved before
   - Use `jive_memory` with `action: "search"` and `memory_type: "troubleshoot"`
   - Match against `ai_use_case` fields for problem descriptions
   - Review solution steps before debugging

**Then create work structure:**

4. **Break down large work hierarchically:**
   - **Initiative** (1-3 months): Major projects or platform changes
   - **Epic** (2-4 weeks): Significant features or capabilities
   - **Feature** (3-5 days): Discrete functionality
   - **Story** (1-2 days): User-facing changes
   - **Task** (1-4 hours): Individual implementation units

5. **Set dependencies and priorities:**
   - Use `jive_get_hierarchy` with `action: "add_dependency"` for work that must be sequenced
   - Mark blocking relationships to prevent out-of-order implementation
   - Set priorities to guide execution order

### Phase 2: Implementation & Documentation

**Track progress actively:**

1. **Update status transitions** - Move work items through: `not_started → in_progress → completed/blocked`
   - Use `jive_track_progress` when starting, pausing, or completing work
   - Add notes explaining what was done or what's blocking progress
   - Update percentage to reflect actual completion (0%, 25%, 50%, 75%, 100%)

2. **Document blockers immediately** - Don't let blocked work go untracked
   - Mark status as `blocked` with blocker details (description + severity)
   - Add estimated completion dates when blockers are resolved
   - Use blocker tracking to surface dependencies to users

**Capture knowledge as you learn:**

3. **Create Architecture Memory when:**
   - You implement a new pattern or approach
   - You make an architectural decision with trade-offs
   - You establish a coding standard or convention
   - You integrate a new library or framework
   - You design a data model or API structure

4. **Create Troubleshooting Memory when:**
   - You spend >30 minutes debugging a problem
   - You encounter a cryptic error message
   - You find a non-obvious solution
   - You discover a gotcha or edge case
   - You fix a problem likely to recur

### Phase 3: Review & Learning

**Use analytics to improve:**

1. **Review progress reports** - Identify bottlenecks and stuck work
   - Use `jive_track_progress` with `action: "get_report"` for status overviews
   - Filter by parent_id to review specific epics or initiatives
   - Look for patterns in blocked items

2. **Analyze trends** - Understand velocity and completion rates
   - Use `action: "get_analytics"` for velocity, burndown, and trends
   - Identify bottlenecks in the development process
   - Adjust planning based on actual completion rates

3. **Export knowledge** - Back up architectural decisions and solutions
   - Use `jive_memory` with `action: "export"` for individual items
   - Use `action: "export_batch"` for bulk exports
   - Store exports as markdown for version control

## Situational Strategies

### Strategy: Starting a New Codebase

1. Create Initiative for the project
2. Search for architecture patterns matching your tech stack
3. Create Epics for: Setup/Infrastructure, Core Features, Testing, Documentation
4. For each Epic, search troubleshooting memory for common pitfalls
5. Create granular tasks under each epic
6. Document architectural decisions as you make them

**Why:** New codebases benefit from structure. Search-first prevents reinventing solutions. Documentation helps maintain consistency.

### Strategy: Adding a Feature to Existing Code

1. Search work items to find related features (understand existing patterns)
2. Review architecture memory for established patterns in the codebase
3. Create Epic or Feature (depending on size)
4. Break into Stories/Tasks
5. Track dependencies on existing work
6. Update architecture memory if you extend or modify patterns

**Why:** Consistency matters in existing codebases. Understanding established patterns prevents architectural drift.

### Strategy: Debugging a Complex Issue

1. Search troubleshooting memory first using error message or problem description
2. If found, apply the documented solution
3. If not found, track your investigation as a task
4. When solved, document in troubleshooting memory with:
   - Exact error message or symptoms (in `ai_use_case`)
   - Root cause analysis
   - Step-by-step solution (in `ai_solutions`)
   - Prevention tips

**Why:** Common problems recur. Documentation saves future debugging time. Error messages make excellent search keys.

### Strategy: Refactoring or Technical Debt

1. Create Epic for the refactoring effort
2. Search architecture memory for target pattern
3. Create Tasks for each module/file to refactor
4. Add dependencies to ensure safe refactoring order
5. Track progress to show incremental improvement
6. Update architecture memory to reflect the new pattern

**Why:** Refactoring is often invisible work. Tracking shows progress. Documentation prevents regression.

### Strategy: Learning a New Technology

1. Search architecture memory for existing usage in the codebase
2. Create Epic "Learn [Technology]" with Stories for key concepts
3. As you learn, document patterns in architecture memory
4. Document gotchas in troubleshooting memory
5. Link learning tasks to real implementation work

**Why:** Structured learning prevents knowledge loss. Documentation helps the next person using the technology.

### Strategy: Working with Dependencies

1. Use `jive_get_hierarchy` to visualize dependency chains before starting work
2. Validate dependencies with `action: "validate"` to catch circular deps
3. Use `relationship_type: "dependents"` to see what's blocked by your work
4. Update dependent work items when you complete blocking work

**Why:** Dependencies cause delays. Understanding them upfront prevents wasted effort on blocked work.

## Best Practices by Tool

### Work Item Management

**Creating Work Items:**
- Use `complexity` field to signal estimation difficulty
- Add `acceptance_criteria` as testable conditions
- Set `priority` based on business value and dependencies
- Use `context_tags` for categorization (e.g., "frontend", "database", "security")

**Searching Work:**
- Use `search_type: "hybrid"` for best results (combines semantic + keyword)
- Use `search_type: "semantic"` for concept-based searches
- Use `search_type: "keyword"` for exact matches (IDs, specific terms)
- Apply filters to narrow by type, status, priority

**Tracking Progress:**
- Update `progress_percentage` in 25% increments as you make real progress
- Use `notes` to explain what changed since last update
- Add `blockers` immediately when work stalls
- Set `estimated_completion` when you can predict it

### Architecture Memory

**Creation Strategy:**
- Use kebab-case slugs: `nextjs-api-auth-pattern`
- Write `ai_requirements` in markdown with code examples
- Add multiple `ai_when_to_use` scenarios (more = better searchability)
- Use `children_slugs` to build pattern hierarchies
- Use `related_slugs` to link similar patterns
- Link to epics with `linked_epic_ids` to track usage

**Search Strategy:**
- Search before every new implementation
- Use natural language: "authentication patterns for REST APIs"
- Review related items (`children_slugs`, `related_slugs`) for comprehensive understanding
- Check `linked_epic_ids` to see real usage examples

**Maintenance:**
- Update patterns when they evolve
- Add new `ai_when_to_use` cases as you discover them
- Link new work to existing patterns
- Export critical patterns for backup

### Troubleshooting Memory

**Creation Strategy:**
- Use error messages in slug: `nextjs-hydration-mismatch-error`
- Include exact error text in `ai_use_case` for search matching
- Write `ai_solutions` with: Problem → Root Cause → Solution → Prevention
- Add code snippets showing the fix
- Tag with all relevant technologies

**Search Strategy:**
- Copy/paste error messages into search queries
- Search by symptom if no error message exists
- Review multiple solutions if found (problem may have multiple causes)
- Use `match_problem` action to find best matching solution

**Maintenance:**
- Update solutions when you find better approaches
- Add new use cases when you encounter variants
- Link related troubleshooting items

## Efficiency Tips

1. **Batch operations** - Create multiple related items in sequence rather than one at a time
2. **Use hierarchy** - Retrieve with `include_children: true` to get full context
3. **Cache searches** - Don't re-search for the same thing multiple times in a session
4. **Update atomically** - Make one update call with all changes rather than multiple calls
5. **Export regularly** - Backup critical architecture and troubleshooting knowledge
6. **Validate early** - Use dependency validation before building deep hierarchies
7. **Filter aggressively** - Use filters to reduce noise in search results
8. **Leverage metadata** - Use tags, keywords, and context tags for better organization

## Common Patterns

### Pattern: Parallel Work Streams

Create separate epics for independent work, use dependencies to link integration points. Track each stream independently, merge at defined integration tasks.

### Pattern: Incremental Delivery

Break large epics into deliverable stories. Mark stories as completed even if epic is ongoing. Track epic progress as percentage of completed stories.

### Pattern: Spike Tasks

Create task-level items for research/investigation with `complexity: "complex"`. Document findings in architecture memory. Convert findings into implementation tasks.

### Pattern: Architectural Decision Records (ADR)

Use architecture memory as ADRs. Include decision context, options considered, trade-offs, and chosen approach. Link to epics that implement the decision.

### Pattern: Bug Triage

Create troubleshooting memory for recurring bugs. Link to fix tasks via epic IDs. Search before investigating new bugs to find known solutions.

## Critical Rules

1. **Search First, Create Second** - Always check existing work and knowledge before starting
2. **Document Decisions, Not Intentions** - Only create architecture memory for implemented patterns
3. **Track Blockers Immediately** - Don't let blocked work go silent
4. **Link Everything** - Use parent-child, dependencies, and epic links to build context
5. **Progress = Truth** - Update percentages based on actual completion, not estimates
6. **Use Error Messages as Keys** - Exact error text makes troubleshooting searchable
7. **One Task, One Focus** - Keep tasks 1-4 hours; break larger work into multiple tasks
8. **Status Reflects Reality** - Don't mark items complete until they truly are

---

**Remember:** MCP Jive makes you systematic, not slow. Use it when structure helps (complex projects, team coordination, knowledge retention). Skip it when it adds overhead (simple fixes, exploration, throwaway code).
