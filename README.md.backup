# MCP Jive - Autonomous AI Code Builder

**🤖 Intelligent Project Management for AI Agents** | **🚀 Streamlined Development Workflows** | **⚡ 8 Consolidated Tools**

[![Latest Release](https://img.shields.io/github/v/release/yourusername/mcp-jive?label=Release&color=brightgreen)](https://github.com/yourusername/mcp-jive/releases/latest)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![LanceDB](https://img.shields.io/badge/Database-LanceDB-orange.svg)](https://lancedb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Semantic Versioning](https://img.shields.io/badge/SemVer-2.0.0-red.svg)](https://semver.org/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org/)

---

## 🎯 **What is MCP Jive?**

MCP Jive is an **autonomous AI code builder** that transforms how AI agents manage development projects. Built on the **Model Context Protocol (MCP)**, it provides intelligent project management capabilities directly within your IDE.

### ✨ **Key Features**

🧠 **AI-Optimized Architecture**
- **8 Consolidated Tools**: Streamlined tools for optimal AI agent performance
- **Autonomous Execution**: AI agents can independently manage entire development workflows
- **Intelligent Context**: Understands project hierarchies, dependencies, and progress patterns

🔍 **Advanced Vector Search**
- **LanceDB Integration**: True embedded vector database with no external dependencies
- **Built-in Vectorization**: Local sentence-transformers with semantic search capabilities
- **Hybrid Search**: Combines semantic similarity with keyword matching for precise results
- **High Performance**: Optimized for fast vector similarity and keyword search

🏗️ **Intelligent Project Structure**
- **Hierarchical Work Items**: Initiative → Epic → Feature → Story → Task
- **Smart Dependencies**: Automatic dependency detection and validation
- **Progress Tracking**: Real-time analytics and completion forecasting
- **Workflow Automation**: Automated execution of development workflows
- **Namespace Support**: Multi-tenant data isolation with namespace-aware operations

## 📦 Installation

### System Requirements

- **Python 3.9+** (Python 3.11+ recommended for best performance)
- **4GB+ RAM** for optimal AI processing
- **MCP-compatible IDE** (VSCode, Cursor, or any IDE with MCP support)

### Quick Installation

**Option 1: Automated Setup (Recommended)**

```bash
# Clone and setup in one command
git clone <repository-url>
cd mcp-jive
./bin/mcp-jive setup environment
```

**Option 2: Manual Installation**

```bash
# 1. Clone the repository
git clone <repository-url>
cd mcp-jive

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install MCP Jive
pip install -r requirements.txt
pip install -e .

# 4. Start the server
./bin/mcp-jive dev server
```

### Verify Installation

```bash
# Start MCP Jive server (combined mode - default for multi-instance access)
./bin/mcp-jive server start

# In another terminal, verify the server is running
curl http://localhost:3454/health
# Should return: {"status": "healthy", "version": "0.1.0"}

# Test the MCP HTTP endpoint (for MCP client integration)
curl -X POST http://localhost:3454/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'
# Should return MCP initialization response

# Alternative: Start development server (uses port 3456)
./bin/mcp-jive dev server
curl http://localhost:3456/health

# Alternative: Start in stdio mode for MCP client integration only (separate instance)
./bin/mcp-jive server start --mode stdio
```

## 🔌 MCP Client Setup

MCP Jive works with any MCP-compatible client. **All clients connect via HTTP to a shared server instance**, enabling seamless data sharing between your IDE, web application, and other MCP clients.

> **Important**: MCP Jive uses a shared server architecture where all clients (IDEs, web app, CLI tools) connect to the same running instance via HTTP. This ensures data consistency and enables real-time collaboration across all interfaces.

Below are step-by-step instructions for all major MCP environments.

### Prerequisites

First, install and start MCP Jive:

```bash
# 1. Clone and install MCP Jive
git clone <repository-url>
cd mcp-jive
./bin/mcp-jive setup environment

# 2. Start the MCP server in combined mode (default)
./bin/mcp-jive server start
# This starts the server on http://localhost:3454 for both web app and MCP clients
```

### Namespace Architecture

**MCP Jive runs a single server that supports multiple namespaces**. Each MCP client registers with a specific namespace for complete data isolation:

#### 🏗️ **Architecture Overview:**
- **One MCP Server** running locally (`http://localhost:3454`)
- **Multiple Namespaces** supported simultaneously
- **Web App** has dropdown to switch between all namespaces
- **Each MCP Client** registers with its own namespace

#### 🔧 **Namespace Configuration Methods**

MCP Jive supports **4 ways** to set namespaces (in priority order):

1. **🥇 URL Path** (Most Compatible): `/mcp/{namespace}` - **RECOMMENDED**
2. **🥈 X-Namespace Header**: `X-Namespace: my-project`
3. **🥉 Request Metadata**: `_meta.namespace` in JSON body
4. **🏅 Tool Arguments**: `namespace` parameter in tool calls

**Why URL Path is Most Compatible:**
- ✅ Supported by **all** MCP client types (no special header support needed)
- ✅ Simple, clean, standard HTTP URL approach
- ✅ Works with basic HTTP clients, curl, and advanced MCP implementations
- ✅ No client-specific configuration requirements

#### 📋 **Compatibility Matrix**

| MCP Client Type | URL Path `/mcp/{ns}` | X-Namespace Header | Dynamic Variables | Recommended |
|-----------------|:-------------------:|:------------------:|:----------------:|:-----------:|
| **VSCode MCP Extension** | ✅ | ✅ | ✅ (`${workspaceFolder:name}`) | URL Path |
| **Cursor IDE** | ✅ | ✅ | ❌ | URL Path |
| **Claude Code** | ✅ | ✅ | ❌ | URL Path |
| **Trae IDE** | ✅ | ✅ | ❌ | URL Path |
| **Kiro IDE** | ✅ | ✅ | ❌ | URL Path |
| **Basic HTTP Clients** | ✅ | ⚠️ (if headers supported) | ❌ | URL Path |
| **Custom MCP Clients** | ✅ | ⚠️ (depends on implementation) | ❌ | URL Path |

**✅ Full Support** | **⚠️ Partial/Depends** | **❌ Not Supported**

#### 📁 **Per-Project MCP Setup (Recommended)**
Each project directory configures its own MCP client with a unique namespace:

```
my-mobile-app/          # Project A
├── .vscode/settings.json   # → namespace: "mobile-app"
└── .cursor/settings.json   # → namespace: "mobile-app"

my-web-dashboard/       # Project B
├── .vscode/settings.json   # → namespace: "web-dashboard"
└── .cursor/settings.json   # → namespace: "web-dashboard"
```

#### 🌍 **Multi-Environment Setup**
Some projects may want multiple environments:
```
my-project/
├── .vscode/settings.json     # → namespace: "my-project-dev"
├── .vscode-staging/          # → namespace: "my-project-staging"
└── .vscode-prod/             # → namespace: "my-project-prod"
```

**Key Benefits:**
- **Complete Data Isolation** between projects
- **Single Server** supports unlimited namespaces
- **Web App Access** to all namespaces via dropdown
- **No Environment Variables** needed

---

### 🔷 VSCode with MCP Extension

**Step 1: Install MCP Extension**
```bash
code --install-extension modelcontextprotocol.mcp
```

**Step 2: Configure Per-Project MCP**

In each project, create `.vscode/settings.json`:

**Basic Per-Project Setup (URL Path Method - Most Compatible):**
```json
{
  "mcp.servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-name"
      }
    }
  }
}
```

**Auto-Namespace from Folder Name (Header Method for VSCode Variables):**
```json
{
  "mcp.servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp",
        "headers": {
          "X-Namespace": "${workspaceFolder:name}"
        }
      }
    }
  }
}
```

**Multi-Environment Project (URL Path Method):**
```json
{
  "mcp.servers": {
    "mcp-jive-dev": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-dev"
      }
    },
    "mcp-jive-staging": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-staging"
      }
    }
  }
}
```

**Step 3: Test Connection**
1. Ensure MCP Jive server is running: `./bin/mcp-jive server start`
2. Open your project in VSCode
3. Run "MCP: List Servers" - you should see `mcp-jive`
4. Run "MCP: List Tools" - you should see 8 jive tools
5. Test: "Create a task for this project" (will use the project's namespace)

---

### 🔶 Cursor IDE

**Step 1: Install MCP Extension**
```bash
cursor --install-extension modelcontextprotocol.mcp
```

**Step 2: Configure Per-Project MCP**

In each project, create `.cursor/settings.json`:

**Basic Per-Project Setup (URL Path Method - Most Compatible):**
```json
{
  "mcp.servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-name"
      }
    }
  }
}
```

**Example for Mobile App Project:**
```json
{
  "mcp.servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/mobile-app"
      }
    }
  }
}
```

**Multi-Environment Project:**
```json
{
  "mcp.servers": {
    "mcp-jive-dev": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/mobile-app-dev"
      }
    },
    "mcp-jive-prod": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/mobile-app-prod"
      }
    }
  }
}
```

**Step 3: Test Connection**
1. Ensure MCP Jive server is running: `./bin/mcp-jive server start`
2. Open your project in Cursor
3. Verify `mcp-jive` server is connected in MCP panel
4. Test: "Create a task for this mobile app project"
5. Verify isolation: Open different project → should show different data

---

### 🔵 Claude Code (Anthropic's CLI)

**Step 1: Install Claude Code**
```bash
npm install -g @anthropic-ai/claude-code
```

**Step 2: Configure Per-Project MCP**

In each project directory, create `.mcp.json`:

```bash
# Create project-specific config
cat > .mcp.json << EOF
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/my-project-name"
    }
  }
}
EOF
```

**Example: Mobile App Project**
```json
{
  "mcpServers": {
    "mcp-jive": {
      "type": "http",
      "url": "http://localhost:3454/mcp/mobile-app"
    }
  }
}
```

**Step 3: Start Claude Code**
```bash
# Ensure MCP Jive server is running
./bin/mcp-jive server start

# Start Claude Code in project directory
cd /path/to/my-project
claude-code
```

**Step 4: Test Integration**
```
# In Claude Code session - will automatically use project namespace
"Create a new epic for user authentication system"
"Show me all work items for this project"
"Add a task for API development"
```

---

### 🔺 Trae IDE

**Step 1: Install Trae IDE**
Download from [Trae IDE website](https://trae.ai)

**Step 2: Configure Per-Project MCP**

In project settings - Go to `Settings > Extensions > MCP Servers`:
```json
{
  "mcp-jive": {
    "type": "http",
    "url": "http://localhost:3454/mcp/my-project-name"
  }
}
```

**Example: E-commerce Project**
```json
{
  "mcp-jive": {
    "type": "http",
    "url": "http://localhost:3454/mcp/ecommerce-platform"
  }
}
```

**Step 3: Enable MCP Jive**
1. Ensure MCP Jive server is running: `./bin/mcp-jive server start`
2. Open your project in Trae IDE
3. Go to `Tools > MCP Servers` and enable `mcp-jive`
4. Test: "Create a feature for product catalog"

---

### 🔸 Kiro IDE

**Step 1: Install Kiro IDE**
Download from [Kiro IDE website](https://kiro.ai)

**Step 2: Configure Per-Project MCP**

In project's `.kiro/config.yaml`:
```yaml
mcp:
  servers:
    mcp-jive:
      transport:
        type: http
        url: http://localhost:3454/mcp/my-project-name
      timeout: 30000
```

**Example: API Project**
```yaml
mcp:
  servers:
    mcp-jive:
      transport:
        type: http
        url: http://localhost:3454/mcp/api-service
      timeout: 30000
```

**Step 3: Test Project Integration**
1. Ensure MCP Jive server is running: `./bin/mcp-jive server start`
2. Open your project in Kiro IDE
3. Test: "Create a task for API endpoint development"

---

### 🟢 OpenAI Codex CLI

**Step 1: Install OpenAI CLI with MCP support**
```bash
pip install openai-mcp-cli
```

**Step 2: Configure Per-Project MCP**

Create `project/.openai-mcp/config.json`:
```json
{
  "mcp_servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-name"
      }
    }
  }
}
```

**Step 3: Start with API Key**
```bash
# Ensure MCP Jive server is running first
./bin/mcp-jive server start

# Start in project directory
export OPENAI_API_KEY="your-api-key"
cd /path/to/my-project
openai-mcp --config .openai-mcp/config.json
```

---

### 🔴 Gemini CLI

**Step 1: Install Gemini CLI with MCP support**
```bash
pip install google-gemini-mcp
```

**Step 2: Configure Per-Project MCP**

Create `project/.gemini/mcp-config.json`:
```json
{
  "servers": {
    "mcp-jive": {
      "transport": {
        "type": "http",
        "url": "http://localhost:3454/mcp/my-project-name"
      }
    }
  }
}
```

**Step 3: Start with API Key**
```bash
# Ensure MCP Jive server is running first
./bin/mcp-jive server start

# Start in project directory
export GOOGLE_API_KEY="your-api-key"
cd /path/to/my-project
gemini-cli --config .gemini/mcp-config.json
```

---

### 🔧 Custom MCP Integration

For custom MCP clients or other tools:

**HTTP Transport (Recommended):**
```bash
# Start MCP Jive server (combined mode - default)
./bin/mcp-jive server start

# MCP endpoint for custom clients
http://localhost:3454/mcp

# Web app endpoint (shares same data)
http://localhost:3454/
```

**Configuration for custom clients:**

**Basic Configuration (Default Namespace):**
```json
{
  "transport": {
    "type": "http",
    "url": "http://localhost:3454/mcp"
  }
}
```

**With Namespace Support (URL Path Method - Most Compatible):**
```json
{
  "transport": {
    "type": "http",
    "url": "http://localhost:3454/mcp/my-custom-namespace"
  }
}
```

**Alternative: Header Method (If URL Path Not Supported):**
```json
{
  "transport": {
    "type": "http",
    "url": "http://localhost:3454/mcp",
    "headers": {
      "X-Namespace": "my-custom-namespace"
    }
  }
}
```


---

### 🔍 Verification Steps

After setting up any MCP client, verify the connection and namespace configuration:

#### 1. **Check Server Connection:**
```bash
# Verify server is running
curl http://localhost:3454/health

# Test MCP endpoint (URL Path Method - Most Compatible)
curl -X POST http://localhost:3454/mcp/test-namespace \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

# Alternative: Header Method
curl -X POST http://localhost:3454/mcp \
  -H "Content-Type: application/json" \
  -H "X-Namespace: test-namespace" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'
```

#### 2. **Verify MCP Client Connection:**
- MCP client should show `mcp-jive` as connected
- No error messages in logs
- Server status shows as "healthy"

#### 3. **List Available Tools:**
Should show 8 jive tools:
- `jive_manage_work_item`
- `jive_get_work_item`
- `jive_search_content`
- `jive_get_hierarchy`
- `jive_execute_work_item`
- `jive_track_progress`
- `jive_sync_data`
- `jive_reorder_work_items`

#### 4. **Test Namespace Isolation:**
```
# Create work items in different namespaces
"Create a task called 'Test Task A' in namespace project-a"
"Create a task called 'Test Task B' in namespace project-b"

# Verify isolation
"List all work items in namespace project-a"
# Should only show "Test Task A"

"List all work items in namespace project-b"
# Should only show "Test Task B"

# Check current namespace
"What namespace am I currently working in?"
```

#### 5. **Test Basic Functionality:**
```
# Basic operations
"Create a new epic for testing MCP integration in this namespace"
"List all work items in my current namespace"
"Show the hierarchy of my current project"

# Cross-namespace verification
"Switch to namespace 'my-other-project'"
"List all work items" # Should show different data
```

#### 6. **Verify Web App Integration:**
1. Open `http://localhost:3454/` in browser
2. Use namespace selector to switch between namespaces
3. Verify work items created via MCP clients appear in web app
4. Create work items in web app and verify they appear in MCP clients

#### 7. **Test Multi-Environment Setup:**
If using multiple environments (dev/staging/prod):
```
# Test dev environment
"Create a task in development environment"
"List all work items in dev namespace"

# Test staging environment
"Create a task in staging environment"
"List all work items in staging namespace"

# Verify isolation between environments
"Compare work items between dev and staging namespaces"
```

### 🐛 Troubleshooting

**Common Issues:**

- **"Server not found"**: Ensure MCP Jive server is running with `./bin/mcp-jive server start`
- **"Connection refused"**: Check if `http://localhost:3454/health` returns a response
- **"Tools not available"**: Verify server started successfully and is accessible at `http://localhost:3454/mcp`
- **"Permission denied"**: Run `chmod +x bin/mcp-jive`
- **"Database errors"**: Ensure `data/` directory is writable
- **"Port already in use"**: Another instance might be running, or use `--port` to specify different port

**Namespace-Specific Issues:**

- **"No work items found"**: Check if you're in the correct namespace
- **"Wrong data returned"**: Verify namespace is set correctly - either URL path `/mcp/{namespace}` or `X-Namespace` header
- **"Namespace isolation not working"**: Ensure each client has unique namespace configuration
- **"Can't switch namespaces"**: Check if MCP client supports dynamic namespace switching

**Verification Commands:**
```bash
# Check if server is running
curl http://localhost:3454/health

# Test MCP endpoint
curl -X POST http://localhost:3454/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

# View server logs
./bin/mcp-jive server start --debug
```

### Configuration

Create a `.env` file in your MCP Jive directory:

```bash
# Copy the example configuration
cp .env.example .env

# Edit configuration as needed
# No external API keys required - uses embedded LanceDB and local processing
```

## 🏢 Namespace Support

MCP Jive includes comprehensive namespace support for multi-tenant data isolation, allowing you to organize work items by project, team, or environment.

### Key Namespace Features

🔒 **Data Isolation**
- Complete separation of work items between namespaces
- Namespace-aware database operations
- Isolated search and analytics

🎯 **Flexible Organization**
- Organize by project, team, client, or environment
- Default namespace for quick setup
- Easy namespace switching in the web UI

⚡ **Seamless Integration**
- Automatic namespace detection from context
- Real-time data refresh on namespace changes
- Consistent namespace handling across all tools

### Namespace Usage

**Web Interface:**
- Use the namespace selector in the top navigation
- Switch between namespaces instantly
- Create new namespaces on-demand

**MCP Tools:**
- All tools automatically respect the current namespace context
- Search and retrieval operations are namespace-scoped
- Progress tracking and analytics per namespace

**Configuration:**
```bash
# Set default namespace
export MCP_JIVE_DEFAULT_NAMESPACE=my-project

# Enable namespace isolation
export MCP_JIVE_NAMESPACE_ISOLATION=true
```

For detailed namespace documentation, see [Namespace Feature Guide](docs/namespace-feature-usage.md).

## 💡 Usage Examples

### Getting Started with MCP Jive

Once MCP Jive is configured in your IDE, you can start using it immediately through natural language commands.

### Project Management

**Create a new project structure:**
```
💬 "Create an initiative for our new mobile app with epics for authentication, user profiles, and notifications in the mobile-app-v2 namespace"

🤖 MCP Jive creates (in mobile-app-v2 namespace):
├── 📋 Initiative: Mobile App Development
│   ├── 📊 Epic: User Authentication System
│   ├── 📊 Epic: User Profile Management
│   └── 📊 Epic: Push Notifications
```

**Break down work automatically:**
```
💬 "Break down the authentication epic into features and stories"

🤖 MCP Jive generates:
├── 📊 Epic: User Authentication System
│   ├── 🎯 Feature: Login/Logout
│   │   ├── 📝 Story: Email/password login
│   │   ├── 📝 Story: Social media login
│   │   └── 📝 Story: Remember me functionality
│   ├── 🎯 Feature: Password Management
│   │   ├── 📝 Story: Password reset
│   │   └── 📝 Story: Password strength validation
```

### Task Automation

**Smart task creation:**
```
💬 "Create tasks for implementing JWT authentication with proper error handling and tests"

🤖 MCP Jive creates:
✅ Task: Implement JWT token generation
✅ Task: Add token validation middleware
✅ Task: Create authentication error handlers
✅ Task: Write unit tests for auth service
✅ Task: Add integration tests for auth endpoints
```

**Dependency management:**
```
💬 "What needs to be completed before we can start the user profile epic?"

🤖 MCP Jive analyzes:
🔍 Dependencies found:
  ✅ User Authentication System (Epic) - In Progress
  ⏳ Database schema design (Task) - Pending
  ⏳ API security framework (Task) - Pending
```

### Progress Tracking

**Real-time insights:**
```
💬 "Show me the progress on our mobile app initiative"

🤖 MCP Jive reports:
📊 Mobile App Development Progress:
  Overall: 34% complete
  🟢 Authentication: 67% (2 of 3 epics done)
  🟡 User Profiles: 12% (planning phase)
  🔴 Notifications: 0% (not started)
  
  🎯 Next Priority: Complete login/logout feature
  ⚠️  Blocker: Database schema needs approval
```

### Workflow Automation

**Automated execution:**
```
💬 "Execute the code review workflow for the authentication feature"

🤖 MCP Jive orchestrates:
1. ✅ Validates all acceptance criteria
2. ✅ Runs automated tests
3. ✅ Checks code quality metrics
4. ✅ Assigns reviewers based on expertise
5. ✅ Creates review checklist
6. ⏳ Schedules follow-up meeting
```

### Available Commands

#### Project Structure
- `"Create an initiative for [project name]"`
- `"Break down [epic/feature] into smaller pieces"`
- `"Show me the hierarchy for [project]"`

#### Task Management
- `"Create a task for [description]"`
- `"What are the dependencies for [task/epic]?"`
- `"Mark [task] as completed"`
- `"Assign [task] to [person]"`

#### Progress & Analytics
- `"Show progress for [project/epic/feature]"`
- `"What's blocking [task/epic]?"`
- `"Generate a status report for [timeframe]"`
- `"Predict completion date for [epic]"`

#### Workflow Execution
- `"Execute [workflow] for [task/feature]"`
- `"Validate completion of [task]"`
- `"Start the review process for [feature]"`

#### Namespace Management
- `"Switch to namespace [name]"`
- `"Create a new namespace for [project]"`
- `"List all available namespaces"`
- `"Show current namespace status"`
- `"Show me all work items in the [project-name] namespace"`
- `"Copy work items from [source-namespace] to [target-namespace]"`
- `"Compare progress between [namespace-a] and [namespace-b]"`

## ⚙️ Configuration

### Environment Variables

MCP Jive can be configured using environment variables. Create a `.env` file:

```bash
# Server Configuration
MCP_JIVE_HOST=localhost
MCP_JIVE_PORT=3454
MCP_JIVE_DEBUG=false
MCP_JIVE_LOG_LEVEL=INFO
MCP_JIVE_AUTO_RELOAD=false

# Database settings (LanceDB embedded by default)
LANCEDB_DATA_PATH=./data/lancedb
LANCEDB_EMBEDDING_MODEL=all-MiniLM-L6-v2
LANCEDB_VECTOR_SIZE=384
LANCEDB_MAX_CONNECTIONS=10


# Security Configuration
MCP_JIVE_SECRET_KEY=your-secret-key-here
MCP_JIVE_ENABLE_AUTH=false
MCP_JIVE_CORS_ORIGINS=*
MCP_JIVE_RATE_LIMIT_REQUESTS=100
MCP_JIVE_RATE_LIMIT_WINDOW=60

# Performance Configuration
MCP_JIVE_WORKERS=1
MCP_JIVE_REQUEST_TIMEOUT=30
MCP_JIVE_ENABLE_METRICS=true
MCP_JIVE_HEALTH_CHECK_INTERVAL=30
MCP_JIVE_ENABLE_PROFILING=false

# Tool Configuration
MCP_JIVE_LEGACY_SUPPORT=true
MCP_JIVE_ENABLE_CACHING=true
MCP_JIVE_MAX_CONCURRENT_EXECUTIONS=3
MCP_JIVE_ENABLE_MIGRATION=true
MCP_JIVE_ENABLE_AI_ORCHESTRATION=true
MCP_JIVE_ENABLE_QUALITY_GATES=true
MCP_JIVE_ENABLE_ANALYTICS=true
MCP_JIVE_ENABLE_WORKFLOW_ORCHESTRATION=true

# Tool Features
MCP_JIVE_ENABLE_TASK_MANAGEMENT=true
MCP_JIVE_ENABLE_WORKFLOW_EXECUTION=true
MCP_JIVE_ENABLE_SEARCH=true
MCP_JIVE_ENABLE_VALIDATION=true
MCP_JIVE_ENABLE_SYNC_TOOLS=true

# Development Configuration
MCP_JIVE_HOT_RELOAD=false
MCP_JIVE_DEBUG_LOGGING=false
MCP_JIVE_TEST_MODE=false
MCP_JIVE_MOCK_AI_RESPONSES=false
MCP_JIVE_ENABLE_TYPE_CHECKING=true
MCP_JIVE_ENABLE_LINTING=true

# Tool Validation Limits
MCP_JIVE_CONTEXT_TAGS_MAX=3
MCP_JIVE_NOTES_MAX_LENGTH=500
MCP_JIVE_ACCEPTANCE_CRITERIA_MAX=5
MCP_JIVE_MAX_RESPONSE_SIZE=10000
MCP_JIVE_TRUNCATION_THRESHOLD=8000
MCP_JIVE_MAX_PARALLEL_EXECUTIONS=3
MCP_JIVE_EXECUTION_TIMEOUT_MINUTES=60
```

### Tool Configuration

MCP Jive now uses consolidated tools exclusively. The legacy tool mode configuration has been removed as part of the architecture simplification.

### Server Configuration

MCP Jive can be configured through environment variables or command-line arguments:

**Command Line Options:**
```bash
# Start with specific configuration
./bin/mcp-jive server start --mode stdio --log-level INFO
./bin/mcp-jive server start --mode http --host 0.0.0.0 --port 3454
./bin/mcp-jive server start --mode combined --port 3454

# Development server (uses port 3456 by default)
./bin/mcp-jive dev server
```

**Tool Mode Configuration:**
```bash
# Set tool mode via environment variable
export MCP_JIVE_TOOL_MODE=consolidated
./bin/mcp-jive dev server
```

**Transport Modes:**
- **stdio**: For MCP client integration (IDEs) - automatically suppresses colored output and banners
- **http**: For REST API access and development
- **combined**: For HTTP server with integrated WebSocket support (default mode)

**Default Mode**: The server runs in `combined` mode by default, providing HTTP API and WebSocket support for multi-instance access. This allows web applications to access the same server instance and view active work items alongside IDE integrations.

**Why Combined Mode as Default?**
- **Multi-Instance Access**: Supports simultaneous connections from IDEs, web apps, and API clients
- **Web App Integration**: Enables web applications to access active work items and real-time updates
- **Unified State**: All clients share the same server instance and database state
- **Real-time Updates**: WebSocket support provides live updates across all connected clients
- **Development Flexibility**: Supports both MCP protocol (stdio) and REST API access simultaneously

**Colored Output Suppression:**
When running in stdio mode for MCP client integration, MCP Jive automatically suppresses:
- Colored terminal output
- Startup banners
- Non-critical logging messages
- Any output that could interfere with JSON-RPC communication

To enable debug output in stdio mode, use:
```bash
./bin/mcp-jive server start --mode stdio --debug
```

## 📚 API Reference

### Available MCP Tools

MCP Jive provides 8 powerful consolidated tools accessible through your IDE, optimized for AI agents and streamlined project management.

#### Consolidated Tools (Core Set)
- `jive_manage_work_item` - Unified CRUD operations for all work item types
- `jive_get_work_item` - Unified retrieval and listing with advanced filtering
- `jive_search_content` - Unified search across all content types (semantic, keyword, hybrid)
- `jive_get_hierarchy` - Unified hierarchy and dependency navigation
- `jive_execute_work_item` - Unified execution for work items and workflows
- `jive_track_progress` - Unified progress tracking and analytics
- `jive_sync_data` - Unified storage and synchronization
- `jive_reorder_work_items` - Unified work item reordering and hierarchy management

The consolidated tools provide comprehensive functionality that previously required multiple legacy tools, offering improved performance and simplified AI agent integration.

### REST API Endpoints

When running as a server, MCP Jive exposes these endpoints:

```bash
# Health and status
GET /health              # Server health check
GET /status              # Detailed server status
GET /metrics             # Performance metrics

# MCP Protocol
GET /tools               # List available MCP tools
POST /mcp                # MCP protocol endpoint

# Documentation
GET /docs                # Interactive API documentation
GET /redoc               # Alternative API documentation
```

### Tool Response Format

All MCP tools return responses in this format:

```json
{
  "success": true,
  "data": {
    // Tool-specific response data
  },
  "message": "Operation completed successfully",
  "metadata": {
    "execution_time": "0.123s",
    "tool_version": "1.0.0"
  }
}
```

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

### How to Contribute

1. **Check out our [Contributing Guide](CONTRIBUTING.md)** for detailed development setup and guidelines
2. **Fork the repository** and create a feature branch
3. **Make your changes** following our coding standards
4. **Submit a pull request** with a clear description of your changes

### Development Setup

For contributors who want to work on MCP Jive itself:

```bash
# Quick development setup
git clone <repository-url>
cd mcp-jive
./bin/mcp-jive setup environment

# Start development server
./bin/mcp-jive dev server
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete development documentation.

### Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read our Code of Conduct before contributing.

## 🆘 Support

### Getting Help

**Quick Troubleshooting:**

```bash
# Check if MCP Jive is running (HTTP mode)
curl http://localhost:3456/health

# Verify your configuration
# API keys are no longer required - using MCP client execution mode

# Verify configuration
python -c "print('MCP Jive uses consolidated tools exclusively')"

# Restart the server
./bin/mcp-jive dev server
```

**Common Issues:**

- **Server not starting**: Check Python 3.9+ and LanceDB database permissions
- **IDE not connecting**: Verify MCP extension installed and `--stdio` flag used
- **Tools not appearing**: Restart IDE and verify MCP extension is properly configured
- **Database errors**: Ensure `data/lancedb` directory is writable
- **Memory issues**: Restart the server if experiencing performance problems

### Community & Resources

- 📖 **Documentation**: [Full documentation](docs/)
- 🏢 **Namespace Guide**: [Namespace Feature Usage](docs/namespace-feature-usage.md)
- 🏗️ **Architecture**: [Namespace Architecture](docs/architecture/namespace-architecture.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **Email**: support@mcp-jive.com

### Enterprise Support

For enterprise deployments and custom integrations, contact us for dedicated support options.

## 📄 License

MCP Jive is open source software licensed under the [MIT License](LICENSE). You're free to use, modify, and distribute it in your projects.

## 🙏 Acknowledgments

Built with love using:
- [Model Context Protocol](https://modelcontextprotocol.io/) - The foundation for IDE integration
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered intelligence
- [LanceDB](https://lancedb.com/) - Embedded vector database for semantic search
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

---

**Ready to supercharge your development workflow? Get started with MCP Jive today! 🚀**

📚 [Full Documentation](docs/) • 🔧 [Contributing Guide](CONTRIBUTING.md) • 💬 [Community Discussions](https://github.com/your-repo/discussions)