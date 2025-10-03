# MCP Jive - AI-Powered Development Workflow Manager

**🤖 Built for Developers using AI Agents** | **🧠 Intelligent Memory System** | **⚡ 8 Consolidated Tools**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![LanceDB](https://img.shields.io/badge/Database-LanceDB-orange.svg)](https://lancedb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is MCP Jive?

**MCP Jive transforms how AI agents manage your development workflow.** It's an intelligent project management system designed specifically for developers who code with AI assistants like Claude, Cursor, and other MCP-compatible tools.

### Why MCP Jive?

When you're building software with AI agents, you need more than a task list. You need:
- **📝 Context Persistence** - AI agents remember architectural decisions and solutions
- **🧠 Smart Memory** - Store patterns, gotchas, and solutions for instant recall
- **🔗 Intelligent Linking** - Connect work items to architecture docs and troubleshooting guides
- **⚡ Built for Speed** - Optimized for AI agent workflows, not manual clicking

---

## ✨ Key Features

### 🧠 **AI Memory System**

The game-changer for AI-powered development. MCP Jive includes two types of persistent memory:

**Architecture Memory**
- 📐 **Store patterns & decisions** - Document how you built features, why you chose specific approaches
- 🔗 **Link to work items** - Connect epics to architectural patterns automatically
- 🎯 **Context-aware retrieval** - AI agents get relevant architecture when implementing features
- 🌲 **Hierarchical organization** - Parent-child relationships for complex architectures

**Troubleshooting Memory**
- 🐛 **Capture solutions** - Save fixes to cryptic errors and gotchas
- 🔍 **Smart matching** - AI agents find solutions based on problem descriptions
- ⚡ **Instant recall** - Never solve the same problem twice
- 📊 **Usage tracking** - See which solutions are most valuable

**How AI Agents Use Memory:**
```
You: "Implement JWT authentication for the API"

AI Agent:
1. Searches Architecture Memory for "jwt" and "authentication"
2. Finds your documented pattern: "jwt-auth-api-pattern"
3. Retrieves implementation details, gotchas, and best practices
4. Implements using your established pattern - consistent every time
```

### 🏗️ **Intelligent Work Structure**

Hierarchical project management designed for how AI agents think:

```
📋 Initiative (1-3 months)
  ├── 📊 Epic (2-4 weeks) ← Links to Architecture Memory
  │   ├── 🎯 Feature (3-5 days)
  │   │   ├── 📝 Story (1-2 days)
  │   │   └── ✅ Task (1-4 hours)
```

- **Auto-dependencies** - AI agents understand what to build first
- **Progress tracking** - Real-time completion analytics
- **Namespace isolation** - Separate projects never mix

### 🔍 **Vector-Powered Search**

Built on LanceDB for lightning-fast semantic search:
- **Hybrid search** - Combines semantic similarity + keywords
- **Finds relevant context** - Even when you don't use exact words
- **Namespace-aware** - Search within project boundaries

---

## 🚀 Quick Start

### Installation (< 2 minutes)

**Prerequisites:** Python 3.9+ and an MCP-compatible IDE (VSCode, Cursor, Claude Code, etc.)

```bash
# 1. Clone and install
git clone <repository-url>
cd mcp-jive
./bin/mcp-jive setup environment

# 2. Start the server
./bin/mcp-jive server start

# 3. Verify it's running
curl http://localhost:3454/health
# Response: {"status": "healthy", "version": "1.2.0"}
```

**That's it!** MCP Jive is now running and ready to connect to your IDE.

---

## 🔌 Connect Your IDE (< 5 minutes)

MCP Jive works with all major AI coding tools. Choose your setup below:

### 🔷 VSCode with Copilot / MCP Extension

**Create `.vscode/mcp.json` in your project:**
```json
{
  "servers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project"
    }
  }
}
```

**Or add globally:** Run `MCP: Add Server` from Command Palette and select "Global".

**Note:** Replace `my-project` with your project name for namespace isolation.

---

### 🔶 Cursor IDE

**Create `.cursor/mcp.json` in your project root:**
```json
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project"
    }
  }
}
```

**Or configure globally:** Create/edit `~/.cursor/mcp.json` with the same structure.

**Note:** Replace `my-project` with your project name for namespace isolation.

---

### 🔵 Claude Code (Anthropic)

**Option 1: Using CLI (Recommended)**
```bash
# Add MCP server for current project
claude mcp add mcp-jive \
  --scope project \
  --type http \
  --url http://localhost:3454/mcp/my-project

# Or add globally for all projects
claude mcp add mcp-jive \
  --scope global \
  --type http \
  --url http://localhost:3454/mcp/my-project
```

**Option 2: Manual Configuration**

Create `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project"
    }
  }
}
```

**Start coding:**
```bash
claude-code
# MCP Jive will be automatically connected
```

**Useful commands:**
```bash
# List configured MCP servers
claude mcp list

# Remove a server
claude mcp remove mcp-jive

# Reset project-scoped server approvals
claude mcp reset-project-choices
```

---

### 🔺 Trae / Kiro / Other MCP IDEs

Most MCP-compatible IDEs follow the standard MCP configuration format.

**Check your IDE's documentation for:**
1. Configuration file location (usually `.mcp.json`, `mcp.json`, or IDE-specific)
2. Whether it uses `"servers"` or `"mcpServers"` key
3. Supported transport types (stdio, http, sse)

**Common formats:**
```json
// Format 1 (VSCode-style)
{
  "servers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/<your-project-name>"
    }
  }
}

// Format 2 (Cursor/Claude Code-style)
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/<your-project-name>"
    }
  }
}
```

---

### ✅ Verify Connection

Ask your AI agent:
```
"List all available tools"
```

You should see 8 `jive_*` tools including:
- ✅ `jive_manage_work_item`
- ✅ `jive_memory` (Architecture & Troubleshooting)
- ✅ `jive_search_content`
- ✅ `jive_get_hierarchy`
- ✅ `jive_track_progress`

---

## 💡 How to Use MCP Jive

### For Developers Using AI Agents

MCP Jive is designed to be used through **natural conversation with your AI agent**. Here's how:

#### 1️⃣ **Plan Your Work**

```
You: "I need to add user authentication to my app"

AI Agent: Creates structured work breakdown:
  📊 Epic: User Authentication System
    ├── 🎯 Feature: Login/Logout
    │   ├── ✅ Task: JWT token generation
    │   ├── ✅ Task: Token validation middleware
    │   └── ✅ Task: Write authentication tests
    ├── 🎯 Feature: Password Management
    └── 🎯 Feature: Session Handling
```

#### 2️⃣ **Document Patterns**

```
You: "Save our JWT implementation as an architecture pattern"

AI Agent: Creates Architecture Memory:
  - Title: "JWT Authentication API Pattern"
  - When to use: REST API authentication, stateless auth required
  - Implementation: [Your documented approach]
  - Gotchas: Token expiry, refresh strategy, secret rotation
  - Links to Epic: User Authentication System
```

#### 3️⃣ **Reuse Knowledge**

```
You: "Implement OAuth for the mobile app"

AI Agent:
  1. Searches Architecture Memory for "authentication" patterns
  2. Finds "JWT Authentication API Pattern"
  3. Adapts the pattern for OAuth
  4. Implements consistently with existing auth approach
```

#### 4️⃣ **Capture Solutions**

```
You: "This CORS preflight error is annoying"

AI Agent: "Let me save this for next time"
  Creates Troubleshooting Memory:
  - Problem: CORS preflight requests failing
  - Solution: Configure Express CORS middleware
  - Code snippet: [Exact fix]
  - Next time: Instant solution, no debugging
```

---

### Common Commands

**Project Management:**
- `"Create an epic for implementing payments"`
- `"Break down the authentication epic into tasks"`
- `"Show me what's blocking the API development"`
- `"What should I work on next?"`

**Using Memory:**
- `"Document our React component pattern as architecture"`
- `"Search architecture memory for database patterns"`
- `"Save the fix for this webpack error to troubleshooting memory"`
- `"Find solutions for Next.js hydration errors"`

**Progress Tracking:**
- `"Show progress on the mobile app initiative"`
- `"Mark the JWT task as completed"`
- `"What's the completion percentage for this sprint?"`
- `"Generate a status report"`

**Namespace Management:**
- `"Switch to the mobile-app namespace"`
- `"List all work items in this project"`
- `"Show me architecture patterns for the backend namespace"`

---

## 🧠 Memory System Deep Dive

### Architecture Memory

**What it stores:**
- Design patterns and approaches
- Technology choices and trade-offs
- Integration guides
- Code conventions and standards
- API designs and data models

**Example Use Cases:**

```
Pattern: "React Form Validation"
└─ When to use: Complex forms, user input validation
└─ Requirements: Use Formik + Yup, custom error handling
└─ Children: "Email Validation", "Password Strength Check"
└─ Linked Epics: User Registration, Profile Editing
```

**AI Agent Benefits:**
- Consistent implementation across features
- No need to re-decide architecture choices
- Instant context when starting new work
- Architectural knowledge persists across sessions

### Troubleshooting Memory

**What it stores:**
- Common errors and solutions
- Configuration gotchas
- Debugging strategies
- Workarounds for library quirks
- Environment setup issues

**Example Use Cases:**

```
Problem: "Module not found after npm install"
└─ Use cases: Build failures, missing dependencies
└─ Solution:
   1. Delete node_modules and package-lock.json
   2. Clear npm cache: npm cache clean --force
   3. Reinstall: npm install
└─ Success rate: 94% (used 17 times)
```

**AI Agent Benefits:**
- Skip repetitive debugging
- Apply proven solutions immediately
- Learn from past mistakes
- Build institutional knowledge

---

## 🎯 Real-World Example Workflow

```
Day 1: Starting a New Feature
──────────────────────────────
You: "I need to add payment processing to the e-commerce app"

AI Agent:
  ✅ Creates Epic: "Payment Processing Integration"
  ✅ Searches Architecture Memory for "payment", "stripe", "api"
  ✅ Finds pattern: "Third-Party API Integration"
  ✅ Creates features: Stripe Setup, Checkout Flow, Webhooks
  ✅ Links Epic to architecture pattern

You: "Start implementing Stripe integration"

AI Agent:
  ✅ Retrieves architecture pattern + implementation guide
  ✅ Implements following your established conventions
  ✅ Marks tasks complete as implementation progresses


Day 2: Hit an Error
────────────────────
You: "Stripe webhook signature validation keeps failing"

AI Agent:
  ✅ Checks Troubleshooting Memory for "stripe webhook"
  ❌ No existing solution found
  ✅ Debugs and solves the issue
  ✅ Saves solution to Troubleshooting Memory

You: "Great, save that fix"


Day 5: New Developer Joins
──────────────────────────────
New Dev: "I need to add PayPal integration"

AI Agent:
  ✅ Searches Architecture Memory: "payment", "api integration"
  ✅ Retrieves: "Third-Party API Integration" + "Stripe Integration"
  ✅ Searches Troubleshooting Memory: "webhook"
  ✅ Finds: "Stripe webhook signature validation"
  ✅ Implements PayPal using proven patterns + avoids known issues
  ✅ Consistent with existing codebase - no architectural drift
```

---

## 🏢 Namespace Isolation

**Each project gets its own isolated data:**

```
Namespaces:
├── mobile-app
│   ├── Work Items: Mobile-specific features
│   ├── Architecture: React Native patterns
│   └── Troubleshooting: Mobile debugging solutions
│
├── backend-api
│   ├── Work Items: API development tasks
│   ├── Architecture: REST API patterns, DB schemas
│   └── Troubleshooting: Server-side errors
│
└── web-dashboard
    ├── Work Items: Dashboard features
    ├── Architecture: Next.js patterns
    └── Troubleshooting: Frontend build issues
```

**Benefits:**
- ✅ Complete data separation
- ✅ Per-project AI context
- ✅ Team-specific patterns
- ✅ No cross-contamination

---

## 📚 Available Tools

MCP Jive provides 8 consolidated tools that AI agents use automatically:

1. **`jive_manage_work_item`** - Create, update, delete work items
2. **`jive_get_work_item`** - Retrieve and list with filtering
3. **`jive_search_content`** - Semantic + keyword search
4. **`jive_get_hierarchy`** - Navigate dependencies and relationships
5. **`jive_execute_work_item`** - Workflow automation
6. **`jive_track_progress`** - Analytics and reporting
7. **`jive_sync_data`** - Backup and synchronization
8. **`jive_memory`** - Architecture & Troubleshooting memory

**You don't call these directly** - your AI agent uses them automatically based on your natural language requests.

---

## 🌐 Web Interface

Access the web UI at `http://localhost:3454/`

**Features:**
- 📊 **Analytics Dashboard** - Visual progress tracking
- 📋 **Work Items** - Manage tasks and epics
- 🧠 **Architecture Memory** - Browse and edit patterns
- 🔧 **Troubleshoot Memory** - Review saved solutions
- 🔄 **Namespace Switcher** - Toggle between projects
- ⚙️ **Settings** - Configure preferences

The web UI shares the same data as your IDE - changes sync in real-time.

---

## ⚙️ Configuration

### Environment Variables

Create `.env` in your MCP Jive directory:

```bash
# Server
MCP_JIVE_PORT=3454
MCP_JIVE_HOST=localhost
MCP_JIVE_DEBUG=false

# Database (LanceDB - embedded, no external DB needed)
LANCEDB_DATA_PATH=./data/lancedb
LANCEDB_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Namespace (optional - can use URL-based namespaces instead)
MCP_JIVE_DEFAULT_NAMESPACE=default
```

### Server Modes

```bash
# Combined mode (default) - Web UI + MCP
./bin/mcp-jive server start

# Development mode (port 3456, with auto-reload)
./bin/mcp-jive dev server

# Production mode with custom port
./bin/mcp-jive server start --port 8080
```

---

## 🐛 Troubleshooting

### Common Issues

**"Server not starting"**
```bash
# Check Python version (need 3.9+)
python --version

# Verify installation
./bin/mcp-jive setup environment

# Check logs
./bin/mcp-jive server start --debug
```

**"IDE can't connect"**
```bash
# Verify server is running
curl http://localhost:3454/health

# Test MCP endpoint
curl -X POST http://localhost:3454/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

**"No tools appearing in IDE"**
1. Restart your IDE
2. Check MCP configuration file exists:
   - VSCode: `.vscode/mcp.json`
   - Cursor: `.cursor/mcp.json` or `~/.cursor/mcp.json`
   - Claude Code: `.mcp.json` in project root
3. Verify correct JSON format for your IDE (see IDE setup sections)
4. Ensure server URL is correct: `http://localhost:3454/mcp/<namespace>`

**"Wrong namespace data"**
- Check your IDE config - each project should have unique namespace
- Verify URL: `http://localhost:3454/mcp/<your-project-name>`
- Use web UI namespace dropdown to confirm correct namespace

### Getting Help

- 📖 **Full Documentation**: [docs/README.md](docs/README.md)
- 🏗️ **Architecture Guide**: [docs/architecture/](docs/architecture/)
- 📋 **AI Agent Instructions**: [docs/guides/agent-jive-instructions.md](docs/guides/agent-jive-instructions.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)

---

## 🤝 Contributing

We welcome contributions! MCP Jive is built by developers for developers.

### Quick Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd mcp-jive
./bin/mcp-jive setup environment

# Start development server (port 3456 with auto-reload)
./bin/mcp-jive dev server

# Run tests
python -m pytest

# Run linting
python -m pylint src/
```

### Contribution Areas

- 🧠 **Memory System** - Enhance AI context retrieval
- 🔍 **Search** - Improve semantic search algorithms
- 🎨 **Web UI** - Frontend improvements
- 📝 **Documentation** - Guides and examples
- 🔌 **Integrations** - New IDE support

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

Free to use, modify, and distribute in your projects.

---

## 🙏 Built With

- **[Model Context Protocol](https://modelcontextprotocol.io/)** - IDE integration foundation
- **[LanceDB](https://lancedb.com/)** - Embedded vector database for semantic search
- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance Python web framework
- **[Next.js](https://nextjs.org/)** - React framework for the web UI
- **[Anthropic Claude](https://www.anthropic.com/)** - AI-powered intelligence

---

## 🚀 Ready to Get Started?

```bash
# 1. Install
git clone <repository-url> && cd mcp-jive
./bin/mcp-jive setup environment

# 2. Start server
./bin/mcp-jive server start

# 3. Configure your IDE (see Quick Start above)

# 4. Start coding with your AI agent!
```

**Join developers using AI agents to build better software, faster.**

---

📚 [Documentation](docs/README.md) • 🔧 [Contributing](CONTRIBUTING.md) • 💬 [Discussions](https://github.com/your-repo/discussions) • 🐛 [Issues](https://github.com/your-repo/issues)
