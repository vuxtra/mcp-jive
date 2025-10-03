# MCP Jive Documentation

Welcome to the comprehensive documentation for **MCP Jive** - an autonomous AI code builder that transforms how AI agents manage development projects.

## 📚 Documentation Structure

This documentation is organized into clear categories for easy navigation:

### 📖 [Guides](guides/)
Step-by-step guides for using and implementing MCP Jive features.

### 📚 [References](references/)
Comprehensive reference documentation for tools and APIs.

### 📝 [Specifications](specifications/)
Technical specifications and data formats.

### 🏗️ [Architecture](architecture/)
System architecture and design documentation.

### 🎯 [Decisions](decisions/)
Architecture Decision Records (ADRs) documenting key technical decisions.

### 📊 [Reports](reports/)
Implementation reports, test results, and validation documentation.

### 📦 [Archive](archive/)
Historical documentation and archived reports.

---

## 🚀 Quick Start

### New Users
1. Start with the [Consolidated Tools Usage Guide](guides/consolidated-tools-usage.md)
2. Review [Agent Jive Instructions](guides/agent-jive-instructions.md) for AI agent usage
3. Check the [Comprehensive MCP Tools Reference](references/comprehensive-mcp-tools-reference.md)

### Developers
1. Read the [Claude Instructions](guides/claude-instructions.md) for development guidelines
2. Study the [Consolidated Tools Implementation Guide](guides/consolidated-tools-implementation.md)
3. Review [Architecture Documentation](architecture/)

### Contributors
1. Follow the [Release Process](guides/release-process.md)
2. Review [Architecture Decision Records](decisions/)
3. Check [Reports](reports/) for system validation

---

## 📖 Guides

Practical guides for using and implementing MCP Jive:

- **[Agent Jive Instructions](guides/agent-jive-instructions.md)** - Complete guide for AI agents using MCP Jive tools
- **[Claude Instructions](guides/claude-instructions.md)** - Development guidelines and project overview for Claude
- **[Consolidated Tools Usage](guides/consolidated-tools-usage.md)** - How to use the 8 consolidated MCP tools
- **[Consolidated Tools Implementation](guides/consolidated-tools-implementation.md)** - Implementation guide for developers
- **[MCP Namespace Binding](guides/mcp-namespace-binding.md)** - Namespace security and client binding
- **[Namespace Feature Usage](guides/namespace-feature-usage.md)** - Using namespaces in frontend and backend
- **[URL Namespace Implementation](guides/url-namespace-implementation.md)** - URL-based namespace parameters
- **[Release Process](guides/release-process.md)** - Automated release workflow
- **[Frontend Setup](guides/frontend-setup.md)** - Frontend application setup and development

---

## 📚 References

Comprehensive reference documentation:

- **[Comprehensive MCP Tools Reference](references/comprehensive-mcp-tools-reference.md)** - Complete documentation of all 8 consolidated tools
- **[Quick Tools Reference](references/quick-tools-reference.md)** - Quick lookup guide for common operations
- **[Releases](references/releases.md)** - Release history and version information

---

## 📝 Specifications

Technical specifications and data formats:

- **[Memory Markdown Format Specification](specifications/memory-markdown-format-spec.md)** - Markdown format for memory export/import
- **[Memory Feature Specification](specifications/memory-feature-spec.md)** - Architecture and troubleshoot memory features

---

## 🏗️ Architecture

System architecture and design documentation:

- **[Namespace Architecture](architecture/namespace-architecture.md)** - Namespace system design and implementation
- **[LanceDB Migration](architecture/lancedb-migration.md)** - Analysis and migration to LanceDB
- **[Consolidated Tools Architecture](architecture/consolidated-tools-architecture.md)** - Tool consolidation design and planning

---

## 🎯 Decisions (ADRs)

Architecture Decision Records documenting key technical choices:

- **[ADR-001: React Framework Selection](decisions/adr-001-react-framework-selection.md)** - Decision to use Next.js for frontend

### Proposed ADRs
Future ADRs to document key decisions:
- ADR-002: Tool Consolidation Strategy
- ADR-003: LanceDB Adoption
- ADR-004: Namespace Architecture

---

## 📊 Reports

Implementation reports and validation documentation:

- **[MCP Jive Comprehensive Test](reports/mcp-jive-comprehensive-test.md)** - Complete system testing report
- **[Consolidation Completed](reports/consolidation-completed.md)** - Tool consolidation completion report
- **[Memory Platform Validation](reports/memory-platform-validation.md)** - Memory system validation results
- **[Frontend Testing Report](reports/frontend-testing-report.md)** - Frontend functionality testing
- **[Web App UI/UX Comprehensive Test](reports/web-app-ui-ux-comprehensive-test.md)** - Complete UI/UX testing results

---

## 🔧 Tool Overview

MCP Jive provides **8 consolidated tools** for AI-powered project management:

1. **`jive_manage_work_item`** - Create, update, delete work items
2. **`jive_get_work_item`** - Retrieve and list work items with filtering
3. **`jive_search_content`** - Semantic, keyword, and hybrid search
4. **`jive_get_hierarchy`** - Navigate hierarchies and dependencies
5. **`jive_execute_work_item`** - Execute work items and workflows
6. **`jive_track_progress`** - Progress tracking and analytics
7. **`jive_sync_data`** - Data synchronization and backup
8. **`jive_memory`** - Architecture and troubleshooting memory

---

## 🎯 Key Features

### 🧠 AI-Optimized
- Designed for autonomous AI agent execution
- Intelligent context understanding
- Smart dependency management

### 🔍 Advanced Search
- Embedded LanceDB vector database
- Semantic similarity search
- Hybrid search capabilities

### 🏗️ Intelligent Structure
- Hierarchical work items (Initiative → Epic → Feature → Story → Task)
- Automatic dependency detection
- Real-time progress tracking

### 🔐 Namespace Support
- Multi-tenant data isolation
- Complete separation between projects
- Flexible organization by project/team/environment

---

## 📋 Documentation Categories

### For Users
- **Getting Started**: [Consolidated Tools Usage Guide](guides/consolidated-tools-usage.md)
- **AI Agent Usage**: [Agent Jive Instructions](guides/agent-jive-instructions.md)
- **Tool Reference**: [Comprehensive MCP Tools Reference](references/comprehensive-mcp-tools-reference.md)

### For Developers
- **Implementation**: [Consolidated Tools Implementation Guide](guides/consolidated-tools-implementation.md)
- **Architecture**: [Architecture Documentation](architecture/)
- **Development**: [Claude Instructions](guides/claude-instructions.md)

### For Administrators
- **Namespace Setup**: [Namespace Feature Usage](guides/namespace-feature-usage.md)
- **Release Management**: [Release Process](guides/release-process.md)
- **System Validation**: [Reports](reports/)

---

## 🔗 Quick Links

### Essential Guides
- [Get Started](guides/consolidated-tools-usage.md) - Begin using MCP Jive
- [Tool Reference](references/comprehensive-mcp-tools-reference.md) - Complete tool documentation
- [Namespace Guide](guides/namespace-feature-usage.md) - Multi-project organization

### Development
- [Implementation Guide](guides/consolidated-tools-implementation.md) - Build with MCP Jive
- [Architecture Docs](architecture/) - System design
- [ADRs](decisions/) - Technical decisions

### Validation
- [Test Reports](reports/) - System validation
- [Specifications](specifications/) - Technical specs

---

## 📝 Contributing to Documentation

When adding or updating documentation:

1. **Place in correct category**:
   - Guides → `/docs/guides/`
   - References → `/docs/references/`
   - Specs → `/docs/specifications/`
   - Architecture → `/docs/architecture/`
   - ADRs → `/docs/decisions/`
   - Reports → `/docs/reports/`

2. **Use kebab-case for filenames**: `my-document-name.md`

3. **Update this README**: Add link in appropriate section

4. **Cross-reference**: Link to related documentation

5. **Keep facts accurate**: Never invent information

---

## 📦 Archive

Historical documentation is preserved in [archive/](archive/) for reference but may be outdated.

---

**Last Updated**: 2025-10-03
**Documentation Version**: 2.0.0
**MCP Jive Version**: 1.2.0
