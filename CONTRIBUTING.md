# Contributing to MCP Jive

We welcome contributions to MCP Jive! This guide will help you get started with development, testing, and contributing to the project.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [IDE Integration](#ide-integration)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing Process](#contributing-process)
- [Troubleshooting](#troubleshooting)

## 🔧 Development Setup

### Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Git** for version control
- **Virtual Environment** support (venv, conda, etc.)
- **4GB+ RAM** for optimal performance
- **10GB+ disk space** for development environment

### Optional but Recommended
- **VSCode** or **Cursor** for enhanced development experience
- **Docker** for containerized deployment
- **Node.js** for frontend development (if applicable)

### Automated Setup (Recommended)

The automated setup script handles everything:

```bash
./bin/mcp-jive setup environment
```

This script will:
- ✅ Create and configure virtual environment
- ✅ Install all dependencies (main + development)
- ✅ Set up configuration files
- ✅ Configure editor settings (VSCode/Cursor)
- ✅ Create test directory structure
- ✅ Generate development utilities
- ✅ Validate the installation

### Manual Setup

If you prefer manual setup:

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .[dev]

# 3. Copy environment configuration
cp .env.example .env.dev

# 4. Create test directories
mkdir -p tests/{unit,integration,mcp}

# 5. Run initial tests
python -m pytest tests/ -v
```

## 🔄 Development Workflow

### Daily Development Commands

```bash
# Start development server with hot reload
./bin/mcp-jive dev server

# Run tests
./bin/mcp-jive dev test
./bin/mcp-jive dev test-unit
./bin/mcp-jive dev test-integration

# Code quality checks
./bin/mcp-jive dev format
./bin/mcp-jive dev lint
./bin/mcp-jive dev type-check

# Run all quality checks
./bin/mcp-jive dev quality

# Check server health
./bin/mcp-jive dev health
```

### Development Server

The development server includes:
- **Hot Reload**: Automatic restart on file changes
- **Enhanced Logging**: Detailed debug information
- **Development Middleware**: Additional debugging tools
- **CORS Configuration**: Enabled for local development

#### Transport Modes

MCP Jive supports four transport modes:

**1. Combined Mode (Default)**
```bash
# Start development server with combined transport (HTTP + WebSocket + STDIO)
./bin/mcp-jive server start
# Server runs on http://localhost:3454 with WebSocket support

# With custom host and port
./bin/mcp-jive server start --host 0.0.0.0 --port 3454
```

**2. HTTP Mode**
```bash
# Start development server with HTTP transport only
./bin/mcp-jive server start --mode http
# Server runs on http://localhost:3454

# With custom host and port
./bin/mcp-jive server start --mode http --host 0.0.0.0 --port 3454
```

**3. STDIO Mode (For MCP Client Integration)**
```bash
# Direct stdio mode
./bin/mcp-jive server start --mode stdio

# With debug logging
./bin/mcp-jive server start --mode stdio --debug

# Test stdio protocol with MCP initialize message
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | ./bin/mcp-jive server start --mode stdio
```

**4. WebSocket Mode**
```bash
# WebSocket transport
./bin/mcp-jive server start --mode websocket --host localhost --port 3455
```

#### STDIO Protocol Development

For developing and testing MCP client integrations:

```bash
# 1. Start stdio server in background for testing
./bin/mcp-jive server start --mode stdio --debug &

# 2. Test with MCP protocol messages
# Initialize the connection
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | ./bin/mcp-jive server start --mode stdio

# List available tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | ./bin/mcp-jive server start --mode stdio

# Call a specific tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jive_manage_work_item","arguments":{"action":"create","type":"task","title":"Test Task","description":"A test task"}}}' | ./bin/mcp-jive server start --mode stdio
```

#### IDE Integration Setup

For VSCode/Cursor MCP extension:

**Combined Mode (Recommended - connects to shared server instance):**
```json
// Add to your MCP client configuration
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

**Stdio Mode (Legacy - separate instance per client):**
```json
// Add to your MCP client configuration
{
  "mcp.servers": {
    "mcp-jive": {
      "command": "python3",
      "args": ["/path/to/mcp-jive/bin/mcp-jive", "server", "stdio"],
      "cwd": "/path/to/mcp-jive"
    }
  }
}
```

```bash
# Start with custom configuration
./bin/mcp-jive server http --host 0.0.0.0 --port 3454 --debug

# Start development mode with hot reload
./bin/mcp-jive server dev --host 0.0.0.0 --port 3456
```

### Environment Management

```bash
# Install/update dependencies
./bin/mcp-jive dev deps
./bin/mcp-jive dev deps --update
./bin/mcp-jive dev deps --dev

# Clean build artifacts
./bin/mcp-jive dev clean

# Reset development database
./bin/mcp-jive dev db-reset
```

## 🔌 IDE Integration

### For MCP Jive Development

When developing MCP Jive itself, you can integrate the development server directly into your IDE for testing and debugging.

#### VSCode/Cursor Integration

1. **Install MCP Extension**
   ```bash
   # Install the MCP extension for VSCode/Cursor
   code --install-extension mcp-client
   ```

2. **Configure Development MCP Server**
   
   Add to your VSCode/Cursor settings (`.vscode/settings.json`):
   ```json
   {
     "mcp.servers": {
       "mcp-jive-dev": {
         "command": "python",
         "args": [
           "/path/to/mcp-jive/src/main.py"
         ],
         "cwd": "/path/to/mcp-jive",
         "env": {
           "MCP_JIVE_ENV": "development",
           "MCP_JIVE_DEBUG": "true"
         }
       }
     }
   }
   ```

3. **Alternative: Use Development Script**
   ```json
   {
     "mcp.servers": {
       "mcp-jive-dev": {
         "command": "python",
         "args": [
           "bin/mcp-jive",
           "--mcp-mode"
         ],
         "cwd": "/path/to/mcp-jive"
       }
     }
   }
   ```

4. **Restart IDE** and the MCP Jive development server will be available in your MCP client.

#### Other IDEs

For other IDEs with MCP support:

1. **Configure MCP Client** to point to the development server:
   - **Command**: `/path/to/mcp-jive/bin/mcp-jive server start --mode stdio`
   - **Working Directory**: `/path/to/mcp-jive`
   - **Environment Variables**:
     - `MCP_JIVE_ENV=development`
     - `MCP_JIVE_DEBUG=true`

   **Note**: Combined mode allows both web app and MCP clients to access the same server instance and shared data. Use `stdio` mode only if you need an isolated instance per client. For general development with web app access, use the default `combined` mode:
   ```bash
   # Default combined mode (recommended for multi-instance development)
   ./bin/mcp-jive server start
   ```

2. **Enable Development Features**:
   ```bash
   # Start with enhanced debugging (stdio mode for MCP clients)
   MCP_JIVE_LOG_LEVEL=DEBUG ./bin/mcp-jive server start --mode stdio
   
   # Start with enhanced debugging (combined mode for web app + MCP)
   MCP_JIVE_LOG_LEVEL=DEBUG ./bin/mcp-jive server start
   ```

#### Development Benefits

- **Live Reload**: Changes to MCP Jive code are reflected immediately
- **Debug Logging**: Enhanced logging for development and debugging
- **Hot Configuration**: Environment changes without restart
- **Development Tools**: Access to additional development-only MCP tools

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_task_management.py
│   ├── test_workflow_engine.py
│   └── ...
├── integration/          # Integration tests
│   ├── test_mcp_server_integration.py
│   ├── test_database_integration.py
│   └── ...
├── mcp/                  # MCP protocol tests
│   ├── test_mcp_protocol.py
│   ├── test_mcp_tools.py
│   └── ...
└── conftest.py          # Shared test configuration
```

### Running Tests

```bash
# Run all tests
./bin/mcp-jive dev test

# Run specific test types
./bin/mcp-jive dev test-unit
./bin/mcp-jive dev test-integration
./bin/mcp-jive dev test-mcp

# Run with coverage
./bin/mcp-jive dev test-coverage
./bin/mcp-jive dev test-coverage --open  # Open coverage report

# Run specific test file
python -m pytest tests/unit/test_task_management.py -v

# Run tests matching pattern
./bin/mcp-jive dev test -k "test_create_task"

# Run tests in parallel
./bin/mcp-jive dev test --parallel
```

### Test Configuration

Tests are configured with:
- **Pytest** as the test runner
- **Coverage** reporting (80% minimum)
- **Custom markers** for test categorization
- **Fixtures** for common test data
- **Mocking** for external dependencies

### Writing Tests

```python
import pytest
from mcp_server.task_management import TaskManager

@pytest.mark.unit
def test_create_task(mock_db):
    """Test task creation functionality."""
    task_manager = TaskManager(mock_db)
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    assert task.title == "Test Task"
    assert task.status == "pending"
```

## 🔍 Code Quality

### Automated Code Quality

```bash
# Format code
./bin/mcp-jive dev format

# Check formatting without changes
./bin/mcp-jive dev format --check

# Run linting
./bin/mcp-jive dev lint

# Type checking
./bin/mcp-jive dev type-check

# Security checks
./bin/mcp-jive dev security

# Run all quality checks
./bin/mcp-jive dev quality
```

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis
- **pre-commit**: Git hooks for quality checks

### Code Standards

- Follow **PEP 8** style guidelines
- Use **type hints** for all functions
- Write **comprehensive tests** (80%+ coverage)
- Include **docstrings** for all public functions
- Keep functions **small and focused** (<50 lines)
- Use **meaningful variable names**

## 🤝 Contributing Process

### Development Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Run** quality checks: `./bin/mcp-jive dev quality`
5. **Run** tests: `./bin/mcp-jive dev test`
6. **Commit** your changes
7. **Push** to your fork
8. **Create** a pull request

### Commit Messages

Use conventional commit format:

```
feat: add new task management feature
fix: resolve database connection issue
docs: update API documentation
test: add integration tests for workflows
refactor: improve error handling
```

### Pull Request Guidelines

- **Clear Description**: Explain what your PR does and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update docs if needed
- **Quality Checks**: Ensure all checks pass
- **Small Changes**: Keep PRs focused and manageable

## 🔧 Troubleshooting

### Common Issues

#### Virtual Environment Issues

```bash
# If virtual environment is not found
./bin/mcp-jive setup environment

# If activation fails
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Dependency Issues

```bash
# Update dependencies
./bin/mcp-jive dev deps --update

# Reinstall from scratch
rm -rf venv
./bin/mcp-jive setup environment
```

#### Database Issues

```bash
# Reset development database
./bin/mcp-jive dev db-reset

# Check Weaviate status
curl http://localhost:8080/v1/meta
```

#### Server Issues

```bash
# Check server health
./bin/mcp-jive dev health

# View server logs
./bin/mcp-jive dev logs
./bin/mcp-jive dev logs --follow
```

#### Test Issues

```bash
# Run tests with verbose output
./bin/mcp-jive dev test -v

# Run specific failing test
python -m pytest tests/unit/test_specific.py::test_function -v -s

# Clear test cache
./bin/mcp-jive dev clean
```

### Getting Help

1. **Check the logs**: `./bin/mcp-jive dev logs`
2. **Run diagnostics**: `./bin/mcp-jive dev version`
3. **Check configuration**: Review `.env.dev` file
4. **Validate setup**: Re-run `./bin/mcp-jive setup environment`
5. **Clean and restart**: `./bin/mcp-jive dev clean && ./bin/mcp-jive dev server`

### Performance Issues

```bash
# Check system resources
./bin/mcp-jive dev health

# Run with profiling
MCP_JIVE_ENABLE_PROFILING=true ./bin/mcp-jive dev server

# Reduce log level
MCP_JIVE_LOG_LEVEL=INFO ./bin/mcp-jive dev server
```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Thank you for contributing to MCP Jive! 🚀**