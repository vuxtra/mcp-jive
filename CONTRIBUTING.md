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
python scripts/setup-dev.py
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
python scripts/dev.py start

# Run tests
python scripts/dev.py test
python scripts/dev.py test-unit
python scripts/dev.py test-integration

# Code quality checks
python scripts/dev.py format
python scripts/dev.py lint
python scripts/dev.py type-check

# Run all quality checks
python scripts/dev.py quality

# Check server health
python scripts/dev.py health
```

### Development Server

The development server includes:
- **Hot Reload**: Automatic restart on file changes
- **Enhanced Logging**: Detailed debug information
- **Development Middleware**: Additional debugging tools
- **CORS Configuration**: Enabled for local development

#### Transport Modes

MCP Jive supports three transport modes:

**1. HTTP Mode (Default for Development)**
```bash
# Start development server with HTTP transport
python scripts/dev.py start
# Server runs on http://localhost:3456
```

**2. STDIO Mode (For MCP Client Integration)**
```bash
# Direct stdio mode
python src/main.py --stdio --log-level INFO

# Or with custom configuration
python src/main.py --stdio --log-level DEBUG --config .env.dev

# Test stdio protocol with MCP initialize message
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python src/main.py --stdio --log-level ERROR
```

**3. WebSocket Mode**
```bash
# WebSocket transport (when implemented)
python src/main.py --websocket --host localhost --port 3456
```

#### STDIO Protocol Development

For developing and testing MCP client integrations:

```bash
# 1. Start stdio server in background for testing
python src/main.py --stdio --log-level INFO &

# 2. Test with MCP protocol messages
# Initialize the connection
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python src/main.py --stdio

# List available tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python src/main.py --stdio

# Call a specific tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jive_create_work_item","arguments":{"type":"task","title":"Test Task","description":"A test task"}}}' | python src/main.py --stdio
```

#### IDE Integration Setup

For VSCode/Cursor MCP extension:

```json
// Add to your MCP client configuration
{
  "mcpServers": {
    "mcp-jive": {
      "command": "python",
      "args": ["/path/to/mcp-jive/src/main.py", "--stdio"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key"
      }
    }
  }
}
```

```bash
# Start with custom configuration
python scripts/dev.py start --host 0.0.0.0 --port 8000 --log-level INFO

# Start without hot reload
python scripts/dev.py start --no-reload
```

### Environment Management

```bash
# Install/update dependencies
python scripts/dev.py deps
python scripts/dev.py deps --update
python scripts/dev.py deps --dev

# Clean build artifacts
python scripts/dev.py clean

# Reset development database
python scripts/dev.py db-reset
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
           "scripts/dev-server.py",
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
   - **Command**: `python /path/to/mcp-jive/src/main.py`
   - **Working Directory**: `/path/to/mcp-jive`
   - **Environment Variables**:
     - `MCP_JIVE_ENV=development`
     - `MCP_JIVE_DEBUG=true`

2. **Enable Development Features**:
   ```bash
   # Start with enhanced debugging
   MCP_JIVE_LOG_LEVEL=DEBUG python src/main.py
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
python scripts/dev.py test

# Run specific test types
python scripts/dev.py test-unit
python scripts/dev.py test-integration
python scripts/dev.py test-mcp

# Run with coverage
python scripts/dev.py test-coverage
python scripts/dev.py test-coverage --open  # Open coverage report

# Run specific test file
python -m pytest tests/unit/test_task_management.py -v

# Run tests matching pattern
python scripts/dev.py test -k "test_create_task"

# Run tests in parallel
python scripts/dev.py test --parallel
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
python scripts/dev.py format

# Check formatting without changes
python scripts/dev.py format --check

# Run linting
python scripts/dev.py lint

# Type checking
python scripts/dev.py type-check

# Security checks
python scripts/dev.py security

# Run all quality checks
python scripts/dev.py quality
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
4. **Run** quality checks: `python scripts/dev.py quality`
5. **Run** tests: `python scripts/dev.py test`
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
python scripts/setup-dev.py

# If activation fails
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### Dependency Issues

```bash
# Update dependencies
python scripts/dev.py deps --update

# Reinstall from scratch
rm -rf venv
python scripts/setup-dev.py
```

#### Database Issues

```bash
# Reset development database
python scripts/dev.py db-reset

# Check Weaviate status
curl http://localhost:8080/v1/meta
```

#### Server Issues

```bash
# Check server health
python scripts/dev.py health

# View server logs
python scripts/dev.py logs
python scripts/dev.py logs --follow
```

#### Test Issues

```bash
# Run tests with verbose output
python scripts/dev.py test -v

# Run specific failing test
python -m pytest tests/unit/test_specific.py::test_function -v -s

# Clear test cache
python scripts/dev.py clean
```

### Getting Help

1. **Check the logs**: `python scripts/dev.py logs`
2. **Run diagnostics**: `python scripts/dev.py version`
3. **Check configuration**: Review `.env.dev` file
4. **Validate setup**: Re-run `python scripts/setup-dev.py`
5. **Clean and restart**: `python scripts/dev.py clean && python scripts/dev.py start`

### Performance Issues

```bash
# Check system resources
python scripts/dev.py health

# Run with profiling
MCP_JIVE_ENABLE_PROFILING=true python scripts/dev.py start

# Reduce log level
MCP_JIVE_LOG_LEVEL=INFO python scripts/dev.py start
```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Thank you for contributing to MCP Jive! 🚀**