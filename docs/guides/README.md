# MCP Jive AI Agent Guides

This directory contains AI agent instruction files for various IDEs and coding tools. These files help AI assistants understand how to effectively use MCP Jive for project management and workflow optimization.

## Quick Reference

### IDE-Specific Instructions

| IDE/Tool | Instruction File | Copy Command |
|----------|-----------------|--------------|
| **VSCode Copilot** | [`.vscode-copilot-instructions.md`](.vscode-copilot-instructions.md) | `cp docs/guides/.vscode-copilot-instructions.md .vscode/` |
| **Cursor** | [`.cursorrules`](.cursorrules) | `cp docs/guides/.cursorrules .` |
| **Claude Code** | [`.claudecoderules`](.claudecoderules) | `cp docs/guides/.claudecoderules .` |
| **Cline** | [`.clinerules`](.clinerules) | `cp docs/guides/.clinerules .` |
| **Windsurf** | [`.windsurfrules`](.windsurfrules) | `cp docs/guides/.windsurfrules .` |
| **Aider** | [`.aiderules`](.aiderules) | `cp docs/guides/.aiderules .` |

### Complete Documentation

- **[`agent-jive-instructions.md`](agent-jive-instructions.md)** - Comprehensive guide for AI agents using MCP Jive
  - Strategic workflows (Planning → Implementation → Review)
  - Situational strategies (new codebase, features, debugging, refactoring)
  - Best practices by tool
  - Common patterns and critical rules

## Usage

### For Developers

1. **Copy the appropriate instruction file to your project root:**
   ```bash
   # Example for Cursor
   cp docs/guides/.cursorrules .cursorrules

   # Example for VSCode
   mkdir -p .vscode
   cp docs/guides/.vscode-copilot-instructions.md .vscode/
   ```

2. **Customize if needed:**
   - Replace `my-project` with your actual project name in URLs
   - Adjust port numbers if not using default 3454
   - Add project-specific guidelines

3. **Start coding with your AI assistant!**

### For AI Agents

When you encounter these instruction files in a project:

1. **Read the file** to understand MCP Jive integration
2. **Follow the workflows** outlined for work item management
3. **Use search-first approach** before creating new work items
4. **Document learnings** in Architecture and Troubleshooting Memory
5. **Track progress** actively as work is completed

## Key Concepts

All instruction files cover these core concepts:

### When to Use MCP Jive
✅ Complex features requiring multi-step implementation
✅ New codebases or major refactors
✅ Architectural patterns worth documenting
✅ Debugging sessions > 30 minutes

❌ Simple bug fixes (< 30 min)
❌ Quick prototypes or exploration
❌ One-line changes

### Core Workflow
1. **Search** → Find existing work and patterns
2. **Check** → Query architecture/troubleshooting memory
3. **Plan** → Create work hierarchy (Epic → Feature → Story → Task)
4. **Execute** → Implement and update progress
5. **Document** → Save patterns and solutions to memory

### Essential MCP Tools

| Tool | Purpose |
|------|---------|
| `jive_search_content` | Search work items and memory (hybrid/semantic/keyword) |
| `jive_manage_work_item` | Create/update work items with acceptance criteria |
| `jive_memory` | Store/retrieve architecture patterns and troubleshooting solutions |
| `jive_track_progress` | Update completion percentage and track blockers |
| `jive_get_hierarchy` | View dependencies and relationships |
| `jive_execute_work_item` | Execute work items and workflows |
| `jive_sync_data` | Backup and restore work items |
| `jive_reorder_work_items` | Reorder and organize work items |

## File Format Details

### `.cursorrules`, `.clinerules`, `.claudecoderules`, `.windsurfrules`, `.aiderules`
- **Format:** Plain text / Markdown
- **Location:** Project root directory
- **Naming:** Starts with `.` (hidden file)
- **Purpose:** Provide context to AI agents about how to use MCP Jive
- **Length:** Concise (< 100 lines) for quick parsing

### `.vscode-copilot-instructions.md`
- **Format:** Markdown
- **Location:** `.vscode/` directory
- **Purpose:** VSCode Copilot-specific instructions
- **Length:** Slightly more detailed with examples

### `agent-jive-instructions.md`
- **Format:** Markdown
- **Location:** `docs/guides/` (reference documentation)
- **Purpose:** Complete guide for AI agents
- **Length:** Comprehensive (280+ lines) with all strategies and patterns

## Server Setup Reminder

Before using MCP Jive with any IDE, ensure the server is running:

```bash
# Start in combined mode (default: stdio + http + websocket)
uvx mcp-jive --port 3454

# Or install with pip first
pip install mcp-jive
mcp-jive --port 3454

# Verify server is running
curl http://localhost:3454/health
```

## Need Help?

- **MCP Jive Issues:** https://github.com/anthropics/mcp-jive/issues
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Main README:** [../../README.md](../../README.md)

---

**Note:** These instruction files are designed to be read by AI agents. They provide context about MCP Jive's capabilities and guide agents to use the tools effectively in your development workflow.
