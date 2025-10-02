# Memory System Markdown Format Specification

**Version:** 1.0
**Date:** 2025-01-XX
**Status:** Official Specification

---

## Overview

This document defines the markdown format for exporting and importing Architecture Memory and Troubleshoot Memory items in the MCP Jive system. The format is designed to be:

1. **Human-readable** - Easy to read and edit in any text editor
2. **Version-controlled** - Works well with Git and other VCS
3. **Portable** - Can be shared across systems and namespaces
4. **Validated** - Strict schema enforcement on import
5. **Lossless** - All data preserved during export/import

---

## Architecture Memory Format

### File Structure

Each architecture item is exported as a separate markdown file with the following naming convention:

```
architecture_{slug}.md
```

### Front Matter (YAML)

The file starts with YAML front matter containing metadata:

```yaml
---
type: architecture
slug: unique-architecture-slug
version: 1.0
created_on: 2025-01-15T10:30:00Z
last_updated_on: 2025-01-15T14:20:00Z
---
```

### Document Structure

```markdown
---
type: architecture
slug: react-component-architecture
version: 1.0
created_on: 2025-01-15T10:30:00Z
last_updated_on: 2025-01-15T14:20:00Z
---

# React Component Architecture

## When to Use

- Building reusable UI components
- Creating component libraries
- Implementing design systems
- Developing React applications

## Keywords

`react`, `components`, `typescript`, `ui`, `frontend`

## Requirements

### Component Structure

All React components should follow this structure:

\`\`\`typescript
interface ComponentProps {
  // Props definition
}

export function Component({ ...props }: ComponentProps) {
  // Implementation
}
\`\`\`

### Best Practices

1. Use functional components with hooks
2. Implement proper TypeScript typing
3. Follow Material-UI patterns
4. Include prop validation

## Relationships

### Children

- `react-hooks-patterns`
- `react-state-management`
- `react-testing`

### Related

- `typescript-patterns`
- `design-system-architecture`

## Epic Links

- `epic-001-frontend-redesign`
- `epic-005-component-library`

## Tags

`architecture`, `react`, `typescript`, `best-practices`

---
*Last updated: 2025-01-15*
```

### Field Mapping

| Markdown Section | Data Model Field | Required | Format |
|-----------------|------------------|----------|--------|
| Front Matter `slug` | `unique_slug` | ✅ | String (kebab-case) |
| Front Matter `created_on` | `created_on` | ✅ | ISO 8601 datetime |
| Front Matter `last_updated_on` | `last_updated_on` | ✅ | ISO 8601 datetime |
| `# Title` (H1) | `title` | ✅ | String |
| `## When to Use` list | `ai_when_to_use` | ❌ | Bullet list |
| `## Keywords` | `keywords` | ❌ | Inline code blocks |
| `## Requirements` | `ai_requirements` | ✅ | Full markdown content |
| `### Children` list | `children_slugs` | ❌ | Bullet list |
| `### Related` list | `related_slugs` | ❌ | Bullet list |
| `## Epic Links` list | `linked_epic_ids` | ❌ | Bullet list |
| `## Tags` | `tags` | ❌ | Inline code blocks |

### Parsing Rules

1. **Front Matter**: Must be valid YAML enclosed in `---` delimiters
2. **Title**: First H1 (`#`) after front matter becomes the title
3. **When to Use**: H2 section with bullet list, one item per line
4. **Keywords**: Inline code blocks separated by commas
5. **Requirements**: All content under H2 "Requirements" until next H2
6. **Children/Related**: Bullet lists under H3 subsections
7. **Epic Links**: Bullet list under H2 section
8. **Tags**: Inline code blocks separated by commas

---

## Troubleshoot Memory Format

### File Structure

Each troubleshoot item is exported as a separate markdown file:

```
troubleshoot_{slug}.md
```

### Front Matter (YAML)

```yaml
---
type: troubleshoot
slug: unique-troubleshoot-slug
version: 1.0
created_on: 2025-01-15T10:30:00Z
last_updated_on: 2025-01-15T14:20:00Z
usage_count: 42
success_count: 38
---
```

### Document Structure

```markdown
---
type: troubleshoot
slug: react-render-loop-fix
version: 1.0
created_on: 2025-01-15T10:30:00Z
last_updated_on: 2025-01-15T14:20:00Z
usage_count: 42
success_count: 38
---

# React Infinite Render Loop

## Problem / Use Cases

- Components re-rendering infinitely
- Browser freezing due to render loop
- useEffect hook causing cascading updates
- State updates triggering immediate re-renders

## Keywords

`react`, `render-loop`, `useEffect`, `performance`, `debugging`

## Solutions

### Root Causes

The most common causes of infinite render loops in React:

1. **Dependency array issues** - Missing or incorrect dependencies
2. **State updates in render** - Calling setState during render phase
3. **Object/array recreations** - New objects in dependency arrays

### Fix 1: Correct useEffect Dependencies

\`\`\`typescript
// ❌ Bad - causes infinite loop
useEffect(() => {
  setCount(count + 1);
});

// ✅ Good - runs once
useEffect(() => {
  setCount(count + 1);
}, []); // Empty dependency array
\`\`\`

### Fix 2: Use useCallback for Functions

\`\`\`typescript
// ❌ Bad - creates new function every render
const handleClick = () => {
  console.log(count);
};

// ✅ Good - memoized function
const handleClick = useCallback(() => {
  console.log(count);
}, [count]);
\`\`\`

### Fix 3: Avoid setState in Render

Never call setState directly during render:

\`\`\`typescript
// ❌ Bad
function Component() {
  setState(newValue); // Causes loop
  return <div>Content</div>;
}

// ✅ Good
function Component() {
  useEffect(() => {
    setState(newValue); // Safe in effect
  }, []);
  return <div>Content</div>;
}
\`\`\`

## Tags

`troubleshooting`, `react`, `performance`, `debugging`

---
*Last updated: 2025-01-15 | Usage: 42 times | Success Rate: 90%*
```

### Field Mapping

| Markdown Section | Data Model Field | Required | Format |
|-----------------|------------------|----------|--------|
| Front Matter `slug` | `unique_slug` | ✅ | String (kebab-case) |
| Front Matter `created_on` | `created_on` | ✅ | ISO 8601 datetime |
| Front Matter `last_updated_on` | `last_updated_on` | ✅ | ISO 8601 datetime |
| Front Matter `usage_count` | `usage_count` | ✅ | Integer |
| Front Matter `success_count` | `success_count` | ✅ | Integer |
| `# Title` (H1) | `title` | ✅ | String |
| `## Problem / Use Cases` list | `ai_use_case` | ✅ | Bullet list |
| `## Keywords` | `keywords` | ❌ | Inline code blocks |
| `## Solutions` | `ai_solutions` | ✅ | Full markdown content |
| `## Tags` | `tags` | ❌ | Inline code blocks |

### Parsing Rules

1. **Front Matter**: Must include usage statistics (`usage_count`, `success_count`)
2. **Title**: First H1 after front matter
3. **Problem/Use Cases**: H2 section with bullet list
4. **Keywords**: Inline code blocks separated by commas
5. **Solutions**: All content under H2 "Solutions" until next H2
6. **Tags**: Inline code blocks separated by commas

---

## Batch Export Format

### Directory Structure

When exporting multiple items, use this structure:

```
export-{namespace}-{timestamp}/
├── metadata.json
├── architecture/
│   ├── architecture_item-1.md
│   ├── architecture_item-2.md
│   └── ...
└── troubleshoot/
    ├── troubleshoot_item-1.md
    ├── troubleshoot_item-2.md
    └── ...
```

### Metadata File (metadata.json)

```json
{
  "export_type": "batch",
  "namespace": "default",
  "export_timestamp": "2025-01-15T10:30:00Z",
  "format": "markdown",
  "version": "1.0",
  "architecture_items": {
    "total": 15,
    "files": [
      "architecture/architecture_item-1.md",
      "architecture/architecture_item-2.md"
    ]
  },
  "troubleshoot_items": {
    "total": 23,
    "files": [
      "troubleshoot/troubleshoot_item-1.md",
      "troubleshoot/troubleshoot_item-2.md"
    ]
  }
}
```

---

## Import Validation

### Required Validations

1. **Front Matter Validation**
   - Must be valid YAML
   - Required fields must be present
   - Dates must be ISO 8601 format
   - Slug must match filename

2. **Content Validation**
   - Title (H1) must be present
   - Required sections must exist
   - Array fields must not exceed max length
   - Text fields must not exceed max length

3. **Slug Validation**
   - Must be unique within namespace
   - Must match pattern: `[a-z0-9-]+`
   - Max length: 100 characters
   - Must match filename (without prefix and extension)

4. **Relationship Validation**
   - Children slugs must reference existing items (warning only)
   - Related slugs must reference existing items (warning only)
   - Epic IDs format validation

### Error Handling

- **Fatal Errors**: Stop import, return error message
  - Invalid YAML
  - Missing required fields
  - Slug conflicts (duplicate)
  - Invalid data types

- **Warnings**: Import succeeds with warnings
  - Missing optional fields
  - Broken relationships (children/related not found)
  - Fields exceeding recommended length
  - Invalid epic ID format

### Import Modes

1. **Create Only** - Only import new items, skip existing slugs
2. **Update Only** - Only update existing items, skip new slugs
3. **Create or Update** - Create new items and update existing (default)
4. **Replace** - Delete existing and create from import

---

## Parsing Libraries

### Python (Backend)

```python
import yaml
import frontmatter  # python-frontmatter package

# Parse markdown with front matter
with open('architecture_item.md', 'r') as f:
    post = frontmatter.load(f)

    metadata = post.metadata  # YAML front matter
    content = post.content    # Markdown content
```

### TypeScript (Frontend)

```typescript
import matter from 'gray-matter';  // gray-matter package

// Parse markdown with front matter
const file = fs.readFileSync('architecture_item.md', 'utf8');
const { data, content } = matter(file);

// data = front matter object
// content = markdown content string
```

---

## Best Practices

### For Humans Editing Files

1. **Always update timestamps** - Update `last_updated_on` when making changes
2. **Maintain slug uniqueness** - Never reuse slugs across items
3. **Use consistent formatting** - Follow the examples exactly
4. **Validate before committing** - Use the import validator before Git commit
5. **Keep relationships accurate** - Update children/related when restructuring

### For Programmatic Export

1. **Always include metadata.json** - Essential for batch imports
2. **Preserve all fields** - Export should be lossless
3. **Use proper encoding** - UTF-8 for all files
4. **Sanitize filenames** - Ensure valid filesystem names
5. **Include version info** - For future format migrations

### For Programmatic Import

1. **Validate first** - Always validate before modifying database
2. **Transaction safety** - Use database transactions for rollback
3. **Report all errors** - Provide detailed error messages
4. **Handle partial imports** - Continue on warnings, stop on errors
5. **Log operations** - Track all imports for auditing

---

## Version History

### Version 1.0 (Current)
- Initial specification
- Support for Architecture and Troubleshoot Memory
- YAML front matter format
- Markdown content structure
- Batch export format

### Future Versions

Planned for version 2.0:
- Binary attachments support
- Relationship validation enforcement
- Schema evolution/migration
- Compression for batch exports
- Incremental export/import

---

## Examples

See the `examples/` directory for complete working examples:
- `examples/architecture_react-patterns.md`
- `examples/troubleshoot_memory-leak.md`
- `examples/batch-export.zip`

---

**Specification Maintained By:** MCP Jive Development Team
**Last Updated:** 2025-01-XX
**Status:** ✅ Official