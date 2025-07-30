# MCP Jive - Agile Task Management for AI Agents

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue.svg)](https://modelcontextprotocol.io/)

**A powerful MCP server that provides comprehensive agile task management capabilities to AI agents through specialized tools and vector-powered search.**

MCP Jive is a Model Context Protocol (MCP) server designed to enhance AI agents with sophisticated project management capabilities. It provides up to 47 specialized tools (16 in minimal mode, 47 in full mode) for managing hierarchical work items, tracking progress, executing workflows, and searching tasks using semantic vector search - all backed by a local embedded Weaviate vector database.

## 🌟 Why Choose MCP Jive?

### 🎯 **Comprehensive Agile Workflow Management**
Provide your AI agents with complete agile project management capabilities:
- **Hierarchical Work Structure**: Initiative → Epic → Feature → Story → Task
- **Flexible Tool Modes**: 16 essential tools (minimal mode) or 47 comprehensive tools (full mode)
- **Dependency Management**: Critical path analysis, bottleneck detection, and circular dependency validation
- **Autonomous Execution Engine**: AI agents can execute work items with progress tracking

### 🧠 **Vector-Powered Task Search**
Advanced search capabilities using embedded vector database:
- **Semantic Search**: Find tasks by meaning, not just keywords
- **Hybrid Search**: Combines vector similarity with keyword matching (BM25)
- **Embedded Weaviate Database**: Self-contained vector database with automatic persistence
- **Real-time Indexing**: Automatic vectorization of task content for instant search

### 🔗 **Native MCP Integration**
Seamless integration with AI agents and development environments:
- **MCP Protocol Compliance**: Works with any MCP-compatible AI agent or IDE
- **Tool Discovery**: AI agents can discover and use all 47 tools automatically
- **Stdio Transport**: Direct integration with IDEs like VSCode and Cursor
- **RESTful API**: Alternative HTTP interface for web-based integrations

### 🔧 **Multi-Provider AI Support**
Flexible AI model integration for autonomous execution:
- **Multiple Providers**: Anthropic Claude, OpenAI GPT, Google Gemini
- **Separate API Keys**: Use different AI models for different tasks
- **Rate Limiting**: Built-in protection against API quota exhaustion
- **Intelligent Routing**: Automatic provider selection based on task requirements

## 🚀 Quick Start

Get up and running in under 10 minutes:

```bash
# 1. Clone the repository
git clone <repository-url>
cd mcp-jive

# 2. Run the automated setup
python scripts/setup-dev.py

# 3. Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Start the development server
python scripts/dev.py start
```

That's it! Your MCP Jive development environment is ready.

## 📋 Table of Contents

- [Why Choose MCP Jive?](#why-choose-mcp-jive)
- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [Installation](#installation)
- [IDE Setup](#ide-setup)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)

## ✨ Key Features

### 🎯 **Hierarchical Task Management**
- **5-Level Hierarchy**: Initiative → Epic → Feature → Story → Task
- **Parent-Child Relationships**: Automatic hierarchy management and validation
- **Progress Rollup**: Child completion automatically updates parent progress
- **Flexible Organization**: Support for complex project structures

### 🔍 **Advanced Search & Discovery**
- **Semantic Vector Search**: Find tasks by meaning using embeddings
- **Hybrid Search**: Combines vector similarity with keyword matching
- **Filtering & Sorting**: Advanced criteria-based filtering
- **Related Item Discovery**: Find semantically similar work items

### ⚡ **Workflow Execution Engine**
- **Autonomous Execution**: AI agents can execute work items independently
- **Progress Tracking**: Real-time monitoring of execution status
- **Dependency Resolution**: Automatic handling of task dependencies
- **Quality Gates**: Validation and approval workflows

### 📊 **Progress & Analytics**
- **Real-time Metrics**: Completion percentages, velocity tracking
- **Bottleneck Detection**: Identify blocking issues and critical paths
- **Milestone Tracking**: Monitor key project milestones
- **Detailed Reporting**: Comprehensive progress summaries

### 💾 **Embedded Vector Database**
- **Embedded Weaviate**: No external database dependencies, runs in-process
- **Automatic Persistence**: Data stored locally in `data/weaviate` directory
- **Schema Management**: Automatic setup of WorkItem and ExecutionLog schemas
- **Health Monitoring**: Built-in database health checks and connection management

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
python scripts/setup-dev.py
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
python scripts/dev.py start
```

### Verify Installation

```bash
# Start MCP Jive server (HTTP mode for development)
python scripts/dev.py start

# Or start in stdio mode for MCP client integration
python scripts/dev.py start-stdio

# Check if MCP Jive is running
curl http://localhost:3456/health

# Should return: {"status": "healthy", "version": "0.1.0"}
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
   
   Add to your IDE settings (`.vscode/settings.json` or `.cursor/settings.json`):
   ```json
   {
     "mcp.servers": {
       "mcp-jive": {
         "command": "python",
         "args": ["/path/to/mcp-jive/src/main.py", "--stdio"],
         "cwd": "/path/to/mcp-jive",
         "env": {
           "ANTHROPIC_API_KEY": "your-api-key-here"
         }
       }
     }
   }
   ```

   **Note**: The `--stdio` flag is essential for MCP client integration. This runs MCP Jive in stdio transport mode, which is required for IDE extensions to communicate with the server.

3. **Test the Connection**:
   ```bash
   # Test stdio mode manually
   python scripts/dev.py start-stdio
   
   # Or test with direct command
   python src/main.py --stdio --log-level INFO
   ```

4. **Restart your IDE** and MCP Jive will be available in the MCP panel

### Other MCP-Compatible IDEs

For other IDEs with MCP support, configure the MCP client to connect to:
- **Command**: `python /path/to/mcp-jive/src/main.py`
- **Working Directory**: `/path/to/mcp-jive`
- **Environment**: Set your AI provider API keys

### Configuration

Create a `.env` file in your MCP Jive directory:

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your API keys
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# GOOGLE_API_KEY=your_key_here
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
# AI Provider API Keys (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Optional: Workspace settings
MCP_JIVE_WORKSPACE=/path/to/your/project
MCP_JIVE_LOG_LEVEL=INFO
MCP_JIVE_MAX_TASKS=100

# Optional: Database settings (for external Weaviate, embedded by default)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your_weaviate_key

# Tool Configuration
MCP_TOOL_MODE=minimal  # Options: minimal (16 tools) or full (47 tools)
```

### Server Configuration

MCP Jive can be configured through environment variables or command-line arguments:

**Command Line Options:**
```bash
# Start with specific configuration
python src/main.py --stdio --log-level INFO
python src/main.py --http --host 0.0.0.0 --port 3456
python src/main.py --websocket --port 8080
```

**Tool Mode Configuration:**
```bash
# Set tool mode via environment variable
export MCP_TOOL_MODE=full  # or minimal
python scripts/dev.py start
```

**Transport Modes:**
- **stdio**: For MCP client integration (IDEs)
- **http**: For REST API access and development
- **websocket**: For real-time applications

## 📚 API Reference

### Available MCP Tools

MCP Jive provides powerful tools accessible through your IDE:
- **Minimal Mode**: 16 essential tools for core functionality
- **Full Mode**: 47 comprehensive tools for advanced workflows

#### Core Task Management Tools (Available in both modes)
- `jive_create_work_item` - Create initiatives, epics, features, stories, or tasks
- `jive_get_work_item` - Retrieve work item details
- `jive_update_work_item` - Update work item properties
- `jive_list_work_items` - List and filter work items
- `jive_search_work_items` - Semantic search across work items

#### Workflow & Dependencies
- `jive_get_work_item_children` - Get child work items
- `jive_get_work_item_dependencies` - Analyze dependencies
- `jive_validate_dependencies` - Check for circular dependencies
- `jive_execute_work_item` - Start autonomous execution
- `jive_get_execution_status` - Monitor execution progress
- `jive_cancel_execution` - Stop and rollback execution

#### Progress & Validation
- `jive_validate_task_completion` - Validate against acceptance criteria
- `jive_approve_completion` - Mark work items as approved

#### Data Synchronization
- `jive_sync_file_to_database` - Sync local files to database
- `jive_sync_database_to_file` - Sync database to local files
- `jive_get_sync_status` - Check synchronization status

### Tool Mode Configuration

**Minimal Mode (16 tools)** - Recommended for most users:
- Essential task management and workflow tools
- Lower memory footprint and faster startup
- Ideal for individual developers and small teams

**Full Mode (47 tools)** - For advanced workflows:
- Complete set of tools including advanced analytics
- File system management and validation tools
- Comprehensive progress tracking and reporting
- Best for enterprise teams and complex projects

To switch modes, set `MCP_TOOL_MODE=full` in your `.env` file and restart the server.

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
    "tool_version": "0.1.0"
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
python scripts/setup-dev.py

# Start development server
python scripts/dev.py start
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
python -c "import os; print('✅ API Key set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing API key')"

# Check tool mode
python -c "import os; print(f'Tool mode: {os.getenv(\"MCP_TOOL_MODE\", \"minimal\")}')"

# Restart the server
python scripts/dev.py start
```

**Common Issues:**

- **Server not starting**: Check Python 3.9+, API keys, and Weaviate database permissions
- **IDE not connecting**: Verify MCP extension installed and `--stdio` flag used
- **Tools not appearing**: Check tool mode setting and restart IDE
- **Database errors**: Ensure `data/weaviate` directory is writable
- **Memory issues**: Switch to minimal mode if experiencing performance problems

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
- [Weaviate](https://weaviate.io/) - Vector database for semantic search
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

---

**Ready to supercharge your development workflow? Get started with MCP Jive today! 🚀**

📚 [Full Documentation](docs/) • 🔧 [Contributing Guide](CONTRIBUTING.md) • 💬 [Community Discussions](https://github.com/your-repo/discussions)