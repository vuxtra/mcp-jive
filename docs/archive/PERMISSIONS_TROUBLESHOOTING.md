# Claude Code MCP Permissions Troubleshooting

## Issue
MCP tool permissions in `.claude/settings.local.json` are not being respected - still being asked for approval despite correct configuration.

## What We've Tried

### 1. ✅ Correct Server-Level Syntax (Per Official Docs)
```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-jive",           // Correct: server-level permission
      "mcp__chrome-devtools"      // Correct: server-level permission
    ]
  }
}
```

**Documentation Reference:**
> "MCP permissions do NOT support wildcards (`*`). To approve all tools from a server, use just the server name (e.g., `mcp__github` instead of `mcp__github__*`)"

### 2. ❌ What Doesn't Work
- `mcp__chrome-devtools__*` - Wildcards not supported
- `mcp__chrome-devtools__take_snapshot` - Individual tool listing (too verbose)

### 3. File Locations Verified

**Settings Precedence (highest to lowest):**
1. `.claude/settings.local.json` ← **We added permissions here** ✅
2. `.claude/settings.json` ← Does not exist
3. `~/.claude/settings.json` ← Exists but no MCP permissions
4. `~/.claude.json` ← Has old chrome-devtools individual tool listings

**Current State:**
- `/Users/fbrbovic/Dev/mcp-jive/.claude/settings.local.json` - Contains correct `mcp__` server-level permissions
- File format is valid JSON
- Syntax matches official documentation examples

## Possible Reasons It's Not Working

### 1. Session/Cache Issue
**Symptom:** Settings take effect immediately per changelog v1.0.90, but many GitHub issues report needing restart

**Solution:** Restart Claude Code completely
- Close all Claude Code sessions
- Quit the application
- Restart and test again

### 2. The /permissions Command
According to search results, there's a `/permissions` command that shows an interactive UI for managing permissions in real-time.

**Try:** Run `/permissions` in Claude Code to see:
- What permissions are actually loaded
- What's being applied vs. what's in the file
- Any conflicts or overrides

### 3. Settings Not Merging Correctly
**Possible Issue:** The project-level `settings.local.json` might not be merging properly with global settings

**Solution:** Try adding the same permissions to `~/.claude.json` instead to see if global-level works:

```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-jive",
      "mcp__chrome-devtools",
      // ... existing permissions
    ]
  }
}
```

### 4. Server Name Mismatch
**Possible Issue:** The MCP server registration name might not match what we're using in permissions

**Verification Needed:**
- Run `/mcp` command to see exact server names as registered
- Server name in permissions MUST exactly match registration name

For example, if the server is registered as `chrome-devtools` but we're using `mcp__chrome-devtools`, there could be a mismatch.

### 5. Permission Format Issue
Some GitHub issues suggest the format might need additional quotes or escaping:

**Try:**
```json
{
  "permissions": {
    "allow": [
      "mcp__mcp-jive",
      "mcp__chrome-devtools"
    ],
    "deny": [],
    "ask": []  // Explicitly empty ask array
  }
}
```

## Recommended Next Steps

1. **Run `/permissions` command** in Claude Code to see actual loaded permissions
2. **Run `/mcp` command** to verify exact MCP server names
3. **Completely restart Claude Code** (quit application, not just close session)
4. **Test with global config** - Add same permissions to `~/.claude.json`
5. **Check for typos** - Verify server names match exactly (case-sensitive)
6. **Use `/doctor` command** - May provide diagnostics about permission issues

## Current Configuration Files

### `/Users/fbrbovic/Dev/mcp-jive/.claude/settings.local.json`
```json
{
  "permissions": {
    "allow": [
      "Read(//Users/fbrbovic/**)",
      "Bash(claude mcp:*)",
      "mcp__mcp-jive",
      "mcp__chrome-devtools",
      "Bash(./scripts/test-release.sh:*)",
      "Bash(while read file)",
      "Bash(do echo \"Moving $file to scripts/temp/\")",
      "Bash(done)",
      "Bash(do echo \"Moving remaining temp file: $file\")",
      "Bash(grep:*)",
      "Bash(xargs:*)",
      "WebSearch",
      "Bash(python3:*)",
      "Bash(find:*)",
      "Bash(curl:*)",
      "Bash(chmod:*)",
      "Bash(/Users/fbrbovic/Dev/mcp-jive/scripts/temp/validate_frontend_components.sh:*)",
      "Bash(pip install:*)",
      "Bash(./bin/mcp-jive:*)",
      "Bash(npm run dev:*)",
      "Bash(lsof:*)",
      "Bash(kill:*)",
      "Bash(sleep:*)",
      "Bash(claude config list:*)"
    ],
    "deny": [],
    "ask": []
  },
  "enableAllProjectMcpServers": true
}
```

## References

- [Claude Code IAM Documentation](https://docs.claude.com/en/docs/claude-code/iam.md)
- [Settings Documentation](https://docs.claude.com/en/docs/claude-code/settings.md)
- [GitHub Issue #395 - settings.local.json auto-approves](https://github.com/ruvnet/claude-flow/issues/395)
- [Scott Spence - Configuring MCP Tools](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)

## Status

❌ **UNRESOLVED** - Configuration is correct per documentation but not taking effect. Needs restart or /permissions verification.