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
         "cwd": "/path/to/mcp-jive"
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
# AI API keys are no longer required - removed in favor of MCP client execution
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
# Workspace settings
MCP_JIVE_WORKSPACE=/path/to/your/project
MCP_JIVE_LOG_LEVEL=INFO
MCP_JIVE_MAX_TASKS=100

# Database settings (LanceDB embedded by default)
LANCEDB_DATA_PATH=/path/to/your/lancedb/data  # Custom data storage path
LANCEDB_EMBEDDING_MODEL=all-MiniLM-L6-v2     # Embedding model for vectorization

# Tool Configuration
MCP_JIVE_TOOL_MODE=consolidated  # Options: consolidated (7 tools), minimal (7+legacy), full (7+all legacy)
```

### Tool Mode Configuration

**Consolidated Mode** (7 tools) - Recommended for new implementations:
```bash
export MCP_JIVE_TOOL_MODE=consolidated
```

**Minimal Mode** (7 consolidated + essential legacy) - For migration period:
```bash
export MCP_JIVE_TOOL_MODE=minimal
```

**Full Mode** (7 consolidated + all legacy tools) - Complete backward compatibility:
```bash
export MCP_JIVE_TOOL_MODE=full
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
export MCP_JIVE_TOOL_MODE=consolidated
python scripts/dev.py start
```

**Transport Modes:**
- **stdio**: For MCP client integration (IDEs)
- **http**: For REST API access and development
- **websocket**: For real-time applications

## 📚 API Reference

### Available MCP Tools

MCP Jive provides powerful consolidated tools accessible through your IDE:
- **Consolidated Mode**: 7 unified tools optimized for AI agents
- **Minimal Mode**: 7 consolidated tools + essential legacy tools for compatibility
- **Full Mode**: 7 consolidated tools + all legacy tools for complete backward compatibility

#### Consolidated Tools (Core Set)
- `jive_manage_work_item` - Unified CRUD operations for all work item types
- `jive_get_work_item` - Unified retrieval and listing with advanced filtering
- `jive_search_content` - Unified search across all content types (semantic, keyword, hybrid)
- `jive_get_hierarchy` - Unified hierarchy and dependency navigation
- `jive_execute_work_item` - Unified execution for work items and workflows
- `jive_track_progress` - Unified progress tracking and analytics
- `jive_sync_data` - Unified storage and synchronization

#### Legacy Tools (Available in Minimal/Full Modes)
The legacy tools are automatically mapped to consolidated tools for backward compatibility:
- Work Item Management: `jive_create_work_item`, `jive_update_work_item`, etc.
- Search & Discovery: `jive_search_work_items`, `jive_search_tasks`, etc.
- Hierarchy & Dependencies: `jive_get_work_item_children`, `jive_validate_dependencies`, etc.
- Execution & Monitoring: `jive_execute_workflow`, `jive_get_execution_status`, etc.
- Progress & Analytics: `jive_get_progress_report`, `jive_set_milestone`, etc.
- Storage & Sync: `jive_sync_file_to_database`, `jive_sync_database_to_file`, etc.

### Tool Mode Comparison

| Mode | Tools | Performance | Use Case |
|------|-------|-------------|----------|
| **Consolidated** | 7 unified tools | Optimal | New implementations, AI agents |
| **Minimal** | 7 + essential legacy | Good | Migration period, mixed environments |
| **Full** | 7 + all 32 legacy | Reduced | Legacy support, transition period |

To switch modes, set `MCP_JIVE_TOOL_MODE` in your `.env` file and restart the server.

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
# API keys are no longer required - using MCP client execution mode

# Check tool mode
python -c "import os; print(f'Tool mode: {os.getenv(\"MCP_JIVE_TOOL_MODE\", \"consolidated\")}')"

# Restart the server
python scripts/dev.py start
```

**Common Issues:**

- **Server not starting**: Check Python 3.9+ and LanceDB database permissions
- **IDE not connecting**: Verify MCP extension installed and `--stdio` flag used
- **Tools not appearing**: Check tool mode setting and restart IDE
- **Database errors**: Ensure `data/lancedb` directory is writable
- **Memory issues**: Switch to consolidated mode if experiencing performance problems

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