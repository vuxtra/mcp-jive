# MCP Jive - Autonomous AI Builder

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

MCP Jive is an autonomous AI builder that leverages the Model Context Protocol (MCP) to create intelligent, context-aware development workflows. It provides a comprehensive suite of tools for task management, workflow execution, progress tracking, and more.

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

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## ✨ Features

### Core Capabilities
- **MCP Protocol Support**: Full implementation of the Model Context Protocol
- **Task Management**: Create, track, and manage development tasks
- **Workflow Execution**: Automated workflow processing with AI integration
- **Progress Tracking**: Real-time progress monitoring and reporting
- **Intelligent Search**: Advanced search capabilities across all data
- **Hierarchy Management**: Organize and manage complex project structures

### AI Integration
- **Multi-Provider Support**: Anthropic Claude, OpenAI GPT, Google Gemini
- **Context-Aware Processing**: Intelligent context management for AI interactions
- **Autonomous Decision Making**: AI-driven task prioritization and execution

### Development Features
- **Hot Reload**: Automatic server restart on code changes
- **Comprehensive Testing**: Unit, integration, and MCP protocol tests
- **Code Quality Tools**: Automated linting, formatting, and type checking
- **Development CLI**: Convenient commands for all development tasks

## 🔧 Prerequisites

- **Python 3.9+** (3.11+ recommended)
- **Git** for version control
- **Virtual Environment** support (venv, conda, etc.)
- **4GB+ RAM** for optimal performance
- **10GB+ disk space** for development environment

### Optional but Recommended
- **VSCode** or **Cursor** for enhanced development experience
- **Docker** for containerized deployment
- **Node.js** for frontend development (if applicable)

## 📦 Installation

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

- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **safety**: Dependency vulnerability checking

### Pre-commit Hooks

Optional pre-commit hooks are available:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## ⚙️ Configuration

### Environment Files

- `.env.dev` - Development configuration (auto-generated)
- `.env.test` - Testing configuration
- `.env.example` - Template for production configuration
- `.env.local` - Local overrides (git-ignored)

### Key Configuration Options

```bash
# Server Configuration
MCP_JIVE_HOST=localhost
MCP_JIVE_PORT=3000
MCP_JIVE_ENV=development

# Database Configuration
WEAVIATE_EMBEDDED=true
WEAVIATE_PERSISTENCE_DATA_PATH=./data/weaviate

# AI Provider Configuration
ANTHROPIC_API_KEY=your_api_key_here
DEFAULT_AI_PROVIDER=anthropic

# Development Settings
MCP_JIVE_DEBUG=true
MCP_JIVE_AUTO_RELOAD=true
MCP_JIVE_LOG_LEVEL=DEBUG
```

### Editor Configuration

VSCode/Cursor settings are automatically configured:
- Python interpreter path
- Linting and formatting settings
- Test discovery
- Debug configurations
- Recommended extensions

## 📚 API Documentation

### MCP Tools

MCP Jive provides 16 essential MCP tools:

1. **Task Management**
   - `create_task` - Create new tasks
   - `get_task` - Retrieve task details
   - `update_task` - Update task information
   - `delete_task` - Remove tasks
   - `list_tasks` - List all tasks

2. **Workflow Execution**
   - `create_workflow` - Create workflow definitions
   - `execute_workflow` - Run workflows
   - `get_workflow_status` - Check workflow progress

3. **Progress Tracking**
   - `update_progress` - Update task/workflow progress
   - `get_progress` - Retrieve progress information

4. **Search & Discovery**
   - `search` - Search across all data
   - `advanced_search` - Complex search queries

5. **Hierarchy Management**
   - `create_hierarchy` - Create organizational structures
   - `update_hierarchy` - Modify hierarchies
   - `get_hierarchy` - Retrieve hierarchy information

6. **System Operations**
   - `health_check` - System health status

### REST API

When running, the server exposes a REST API:

```bash
# Health check
GET /health

# MCP endpoint
POST /mcp

# API documentation
GET /docs
GET /redoc
```

## 🤝 Contributing

### Development Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Run** quality checks: `python scripts/dev.py quality`
5. **Run** tests: `python scripts/dev.py test`
6. **Commit** your changes
7. **Push** to your fork
8. **Create** a pull request

### Code Standards

- Follow **PEP 8** style guidelines
- Use **type hints** for all functions
- Write **comprehensive tests** (80%+ coverage)
- Include **docstrings** for all public functions
- Keep functions **small and focused** (<50 lines)
- Use **meaningful variable names**

### Commit Messages

Use conventional commit format:

```
feat: add new task management feature
fix: resolve database connection issue
docs: update API documentation
test: add integration tests for workflows
refactor: improve error handling
```

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the foundational protocol
- [Anthropic](https://www.anthropic.com/) for Claude AI integration
- [Weaviate](https://weaviate.io/) for vector database capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

**Happy Coding! 🚀**

For more information, visit our [documentation](docs/) or check out the [API reference](docs/api/).