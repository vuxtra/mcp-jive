# MCP Jive - Autonomous AI Code Builder

**🤖 Intelligent Project Management for AI Agents** | **🚀 Streamlined Development Workflows** | **⚡ 7 Consolidated Tools**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![LanceDB](https://img.shields.io/badge/Database-LanceDB-orange.svg)](https://lancedb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 **What is MCP Jive?**

MCP Jive is an **autonomous AI code builder** that transforms how AI agents manage development projects. Built on the **Model Context Protocol (MCP)**, it provides intelligent project management capabilities directly within your IDE.

### ✨ **Key Features**

🧠 **AI-Optimized Architecture**
- **7 Consolidated Tools**: Streamlined from 32+ legacy tools for optimal AI agent performance
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

## 🔌 IDE Setup

### VSCode/Cursor Setup

1. **Install MCP Extension** (if not already installed)
   ```bash
   # For VSCode
   code --install-extension mcp-client
   
   # For Cursor
   cursor --install-extension mcp-client
   ```

2. **Configure MCP Jive Server**
   
   **For Combined Mode (Recommended - connects to shared server instance):**
   
   Add to your IDE settings (`.vscode/settings.json` or `.cursor/settings.json`):
   ```json
   {
     "mcp.servers": {
       "mcp-jive": {
         "transport": {
           "type": "http",
           "url": "http://localhost:3454/mcp"
         }
       }
     }
   }
   ```
   
   **For Stdio Mode (Legacy - separate instance per client):**
   ```json
   {
     "mcp.servers": {
       "mcp-jive": {
         "command": "/path/to/mcp-jive/bin/mcp-jive",
         "args": ["server", "start", "--mode", "stdio"],
         "cwd": "/path/to/mcp-jive"
       }
     }
   }
   ```

   **Note**: Combined mode allows both web app and MCP clients to access the same server instance and shared data. Use stdio mode only if you need an isolated instance per client.

3. **Start the Server** (Required for Combined Mode):
   ```bash
   # Start combined mode server (required for HTTP transport)
   ./bin/mcp-jive server start
   
   # Or with custom host/port
   ./bin/mcp-jive server start --host 0.0.0.0 --port 3454
   
   # Test stdio mode for MCP client integration only (separate instance)
   ./bin/mcp-jive server start --mode stdio
   
   # Or with debug logging
   ./bin/mcp-jive server start --mode stdio --debug
   ```
   
   **Note**: For combined mode, the server must be running separately before MCP clients can connect to the HTTP endpoint.

4. **Restart your IDE** and MCP Jive will be available in the MCP panel

### Other MCP-Compatible IDEs

For other IDEs with MCP support, configure the MCP client to connect to:

**Combined Mode (Recommended):**
- **Transport**: HTTP
- **URL**: `http://localhost:3454/mcp`
- **Note**: Requires server to be running separately with `./bin/mcp-jive server start`

**Stdio Mode (Legacy):**
- **Command**: `/path/to/mcp-jive/bin/mcp-jive server start --mode stdio`
- **Working Directory**: `/path/to/mcp-jive`
- **Environment**: Set your AI provider API keys

### Configuration

Create a `.env` file in your MCP Jive directory:

```bash
# Copy the example configuration
cp .env.example .env

# Edit configuration as needed
# No external API keys required - uses embedded LanceDB and local processing
```

## 💡 Usage Examples

### Getting Started with MCP Jive

Once MCP Jive is configured in your IDE, you can start using it immediately through natural language commands.

### Project Management

**Create a new project structure:**
```
💬 "Create an initiative for our new mobile app with epics for authentication, user profiles, and notifications"

🤖 MCP Jive creates:
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

MCP Jive provides 7 powerful consolidated tools accessible through your IDE, optimized for AI agents and streamlined project management.

#### Consolidated Tools (Core Set)
- `jive_manage_work_item` - Unified CRUD operations for all work item types
- `jive_get_work_item` - Unified retrieval and listing with advanced filtering
- `jive_search_content` - Unified search across all content types (semantic, keyword, hybrid)
- `jive_get_hierarchy` - Unified hierarchy and dependency navigation
- `jive_execute_work_item` - Unified execution for work items and workflows
- `jive_track_progress` - Unified progress tracking and analytics
- `jive_sync_data` - Unified storage and synchronization

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