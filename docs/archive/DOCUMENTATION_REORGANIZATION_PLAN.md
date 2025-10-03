# Documentation Reorganization Plan

**Date**: 2025-10-03
**Purpose**: Comprehensive reorganization of all markdown documentation
**Goal**: Structured documentation with clear categories

---

## Current State Analysis

### Files Found: 91 markdown files total

**Location Breakdown:**
- Root: 8 files
- docs/: 13 files (production)
- docs/temp/: 45 files (archived/temporary)
- docs/architecture/: 2 files
- docs/specs/: 1 file
- .trae/: 16 files (IDE-specific, external)
- frontend/: 1 file
- scripts/temp/: 1 file
- src/mcp_jive/planning/prompts/: 4 files (code templates)
- .pytest_cache/: 1 file (tool-generated)

---

## Reorganization Strategy

### Target Structure

```
/
├── README.md                          [ROOT - Keep as main entry]
├── CHANGELOG.md                       [ROOT - Version history]
├── CONTRIBUTING.md                    [ROOT - Contribution guide]
├── docs/
│   ├── README.md                      [NEW - Documentation index]
│   ├── guides/
│   │   ├── agent-jive-instructions.md
│   │   ├── claude-instructions.md
│   │   ├── consolidated-tools-usage.md
│   │   ├── consolidated-tools-implementation.md
│   │   ├── mcp-namespace-binding.md
│   │   ├── namespace-feature-usage.md
│   │   ├── url-namespace-implementation.md
│   │   ├── release-process.md
│   │   └── frontend-setup.md
│   ├── references/
│   │   ├── comprehensive-mcp-tools-reference.md
│   │   ├── quick-tools-reference.md
│   │   └── releases.md
│   ├── specifications/
│   │   ├── memory-markdown-format-spec.md
│   │   └── memory-feature-spec.md
│   ├── architecture/
│   │   ├── namespace-architecture.md
│   │   ├── lancedb-migration.md
│   │   └── consolidated-tools-architecture.md
│   ├── decisions/
│   │   ├── adr-001-react-framework-selection.md
│   │   ├── adr-002-tool-consolidation.md
│   │   └── adr-003-lancedb-adoption.md
│   ├── reports/
│   │   ├── consolidation-completed.md
│   │   ├── memory-platform-validation.md
│   │   ├── frontend-testing-report.md
│   │   └── web-app-ui-ux-comprehensive-test.md
│   └── archive/
│       └── [All temp files stay here]
```

---

## File Categorization

### ROOT LEVEL (Keep in place)
- ✅ `README.md` - Main project README
- ✅ `CHANGELOG.md` - Version history
- ✅ `CONTRIBUTING.md` - Contribution guidelines

### GUIDES → /docs/guides/
- `AGENT-JIVE-INSTRUCTIONS.md` → `agent-jive-instructions.md`
- `CLAUDE.md` → `claude-instructions.md`
- `CONSOLIDATED_TOOLS_USAGE_GUIDE.md` → `consolidated-tools-usage.md`
- `CONSOLIDATED_TOOLS_IMPLEMENTATION_GUIDE.md` → `consolidated-tools-implementation.md`
- `mcp-namespace-binding.md` → (keep same)
- `namespace-feature-usage.md` → (keep same)
- `URL_NAMESPACE_IMPLEMENTATION.md` → `url-namespace-implementation.md`
- `RELEASE_PROCESS.md` → `release-process.md`
- `frontend/README.md` → `frontend-setup.md`

### REFERENCES → /docs/references/
- `comprehensive_mcp_tools_reference.md` → `comprehensive-mcp-tools-reference.md`
- `quick_tools_reference.md` → `quick-tools-reference.md`
- `RELEASES.md` → `releases.md`

### SPECIFICATIONS → /docs/specifications/
- `MEMORY_MARKDOWN_FORMAT_SPEC.md` → `memory-markdown-format-spec.md`
- `specs/memory.md` → `memory-feature-spec.md`

### ARCHITECTURE → /docs/architecture/
- `architecture/namespace-architecture.md` → (keep)
- `docs/temp/LANCEDB_MIGRATION_ANALYSIS.md` → `lancedb-migration.md`
- `docs/temp/CONSOLIDATION_PLAN.md` → `consolidated-tools-architecture.md`

### DECISIONS (ADRs) → /docs/decisions/
- `architecture/decisions/adr-001-react-framework-selection.md` → (keep)
- NEW: Create ADR for tool consolidation
- NEW: Create ADR for LanceDB adoption

### REPORTS → /docs/reports/
- `docs/temp/CONSOLIDATION_COMPLETED.md` → `consolidation-completed.md`
- `docs/temp/MEMORY_PLATFORM_VALIDATION_REPORT.md` → `memory-platform-validation.md`
- `docs/temp/FRONTEND_TESTING_REPORT.md` → `frontend-testing-report.md`
- `docs/temp/WEB_APP_UI_UX_COMPREHENSIVE_TEST.md` → `web-app-ui-ux-comprehensive-test.md`
- `MCP_JIVE_COMPREHENSIVE_TEST.md` → `mcp-jive-comprehensive-test.md`

### ARCHIVE → /docs/archive/ (Keep all temp files)
- All remaining `docs/temp/*` files

### EXCLUDE (Tool-generated, IDE-specific, code templates)
- `.trae/*` - IDE-specific files (external to main docs)
- `.pytest_cache/README.md` - Tool-generated
- `src/mcp_jive/planning/prompts/*.md` - Code templates (not documentation)
- `scripts/temp/README.md` - Script documentation (keep in scripts/)

---

## Implementation Steps

1. ✅ Create new directory structure
2. ✅ Move and rename files systematically
3. ✅ Update all internal cross-references
4. ✅ Create comprehensive /docs/README.md
5. ✅ Verify all links work
6. ✅ Update root README.md to point to /docs/

---

## File Movement Matrix

| Current Location | New Location | Rename |
|-----------------|--------------|--------|
| `AGENT-JIVE-INSTRUCTIONS.md` | `docs/guides/agent-jive-instructions.md` | Yes |
| `CLAUDE.md` | `docs/guides/claude-instructions.md` | Yes |
| `RELEASES.md` | `docs/references/releases.md` | No |
| `MCP_JIVE_COMPREHENSIVE_TEST.md` | `docs/reports/mcp-jive-comprehensive-test.md` | Yes |
| ... (see full matrix below) | ... | ... |

---

## Cross-Reference Updates Needed

Files with internal links that need updating:
1. `README.md` - Update all docs links
2. `docs/README.md` - Create with all new paths
3. `CONTRIBUTING.md` - Update docs references
4. All moved files - Update relative paths

---

## Status

**Planning Phase**: Complete
**Ready for Implementation**: Yes
