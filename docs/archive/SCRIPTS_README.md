# MCP Jive Scripts Organization

This document describes the reorganized script structure for the MCP Jive project, providing a unified command-line interface and better organization of development tools.

## Quick Start

The unified CLI entry point is located at `bin/mcp-jive`. Make it executable and use it for all operations:

```bash
# Make the CLI executable (if not already)
chmod +x bin/mcp-jive

# View available commands
./bin/mcp-jive --help

# Start development server
./bin/mcp-jive dev server

# Reset database
./bin/mcp-jive dev db-reset

# Run health check
./bin/mcp-jive tools health-check
```

## Directory Structure

```
├── bin/
│   └── mcp-jive              # Unified CLI entry point
├── scripts/
│   ├── dev/                  # Development utilities
│   │   ├── database.py       # Database operations (reset, etc.)
│   │   ├── logs.py          # Log viewing and filtering
│   │   └── server.py        # Development server with hot-reload
│   ├── server/              # Server management
│   │   ├── start.py         # Unified server startup
│   │   └── stdio.py         # STDIO mode server
│   ├── setup/               # Installation and setup
│   │   ├── environment.py   # Environment setup
│   │   ├── install.py       # Dependency installation
│   │   └── lancedb.py       # LanceDB setup
│   └── testing/             # Testing utilities
│       ├── e2e.py          # End-to-end test runner
│       └── e2e-test.sh     # Original E2E test script
└── tools/                   # Utility tools
    ├── backup_restore.py    # Backup and restore operations
    ├── health_check.py     # System health checks
    └── validate_config.py  # Configuration validation
```

## Unified CLI Commands

### Server Operations

```bash
# Start server in different modes
./bin/mcp-jive server start --mode stdio
./bin/mcp-jive server start --mode http --port 8080
./bin/mcp-jive server start --mode websocket

# Start with consolidated tools
./bin/mcp-jive server start --consolidated

# Start with debug mode
./bin/mcp-jive server start --debug
```

### Development Operations

```bash
# Start development server with hot-reload
./bin/mcp-jive dev server

# Database operations
./bin/mcp-jive dev db-reset
./bin/mcp-jive dev db-status

# View logs
./bin/mcp-jive dev logs
./bin/mcp-jive dev logs --follow
./bin/mcp-jive dev logs --level ERROR
```

### Setup Operations

```bash
# Full environment setup
./bin/mcp-jive setup environment

# Install dependencies
./bin/mcp-jive setup install

# Setup LanceDB
./bin/mcp-jive setup lancedb
```

### Testing Operations

```bash
# Run end-to-end tests
./bin/mcp-jive test e2e

# Run with specific options
./bin/mcp-jive test e2e --verbose --timeout 300
```

### Utility Tools

```bash
# Health check
./bin/mcp-jive tools health-check
./bin/mcp-jive tools health-check --detailed
./bin/mcp-jive tools health-check --json

# Configuration validation
./bin/mcp-jive tools validate-config
./bin/mcp-jive tools validate-config --env

# Backup operations
./bin/mcp-jive tools backup create
./bin/mcp-jive tools backup restore backup_file.tar.gz
./bin/mcp-jive tools backup list backup_file.tar.gz
```

## Individual Script Usage

While the unified CLI is recommended, individual scripts can still be used directly:

### Development Scripts

```bash
# Development server
python scripts/dev/server.py

# Database operations
python scripts/dev/database.py db-reset
python scripts/dev/database.py db-status

# Log viewer
python scripts/dev/logs.py --follow --level INFO
```

### Server Scripts

```bash
# Unified server start
python scripts/server/start.py --mode stdio
python scripts/server/start.py --mode http --port 8080

# STDIO server
python scripts/server/stdio.py
```

### Setup Scripts

```bash
# Environment setup
python scripts/setup/environment.py

# Install dependencies
python scripts/setup/install.py

# LanceDB setup
python scripts/setup/lancedb.py
```

### Testing Scripts

```bash
# End-to-end tests
python scripts/testing/e2e.py
python scripts/testing/e2e.py --verbose

# Original shell script
bash scripts/testing/e2e-test.sh
```

### Utility Tools

```bash
# Health check
python tools/health_check.py
python tools/health_check.py --detailed --json

# Configuration validation
python tools/validate_config.py
python tools/validate_config.py --env --verbose

# Backup and restore
python tools/backup_restore.py backup
python tools/backup_restore.py restore backup_file.tar.gz
python tools/backup_restore.py list backup_file.tar.gz
python tools/backup_restore.py clean --days 30
```

## Migration from Old Scripts

### Old → New Mapping

| Old Script | New Location | Unified CLI Command |
|------------|--------------|--------------------|
| `scripts/dev.py` | `scripts/dev/database.py` | `./bin/mcp-jive dev db-reset` |
| `scripts/dev-server.py` | `scripts/dev/server.py` | `./bin/mcp-jive dev server` |
| `scripts/mcp-stdio-server.py` | `scripts/server/stdio.py` | `./bin/mcp-jive server start --mode stdio` |
| `scripts/setup-dev.py` | `scripts/setup/install.py` | `./bin/mcp-jive setup install` |
| `scripts/setup_lancedb.py` | `scripts/setup/lancedb.py` | `./bin/mcp-jive setup lancedb` |
| `scripts/e2e-test.sh` | `scripts/testing/e2e-test.sh` | `./bin/mcp-jive test e2e` |
| `mcp-server.py` | `scripts/server/start.py` | `./bin/mcp-jive server start` |
| `run_consolidated_server.sh` | `scripts/server/start.py --consolidated` | `./bin/mcp-jive server start --consolidated` |

### Backward Compatibility

The unified CLI includes fallback mechanisms to existing scripts if the new reorganized scripts are not yet fully in place. This ensures a smooth transition.

## Features and Benefits

### Unified Interface
- Single entry point for all operations
- Consistent command structure
- Built-in help and documentation
- Standardized argument parsing

### Better Organization
- Logical grouping by function
- Clear separation of concerns
- Easier maintenance and discovery
- Reduced script duplication

### Enhanced Functionality
- Improved error handling
- Better logging and output
- More configuration options
- Comprehensive help system

### Development Experience
- Hot-reload development server
- Real-time log viewing
- Comprehensive health checks
- Easy environment setup

## Environment Variables

The scripts respect these environment variables:

```bash
# Server configuration
MCP_JIVE_HOST=localhost
MCP_JIVE_PORT=8000
MCP_JIVE_DEBUG=true
MCP_JIVE_LOG_LEVEL=INFO

# Database configuration
MCP_JIVE_DATA_DIR=./data

# Tool configuration
MCP_JIVE_CONSOLIDATED_TOOLS=false
MCP_JIVE_AI_ENABLED=true
```

## Configuration Files

Scripts can use configuration files in the `config/` directory:

- `config/development.json` - Development settings
- `config/production.json` - Production settings
- `config/testing.json` - Testing settings

## Troubleshooting

### Common Issues

1. **Permission denied**: Make sure scripts are executable
   ```bash
   chmod +x bin/mcp-jive
   chmod +x scripts/**/*.py
   chmod +x tools/*.py
   ```

2. **Module not found**: Ensure you're in the project root directory
   ```bash
   cd /path/to/mcp-jive
   ./bin/mcp-jive --help
   ```

3. **Database issues**: Reset the database
   ```bash
   ./bin/mcp-jive dev db-reset
   ```

4. **Environment issues**: Run environment setup
   ```bash
   ./bin/mcp-jive setup environment
   ```

### Health Check

Run a comprehensive health check to diagnose issues:

```bash
./bin/mcp-jive tools health-check --detailed
```

### Getting Help

```bash
# General help
./bin/mcp-jive --help

# Command-specific help
./bin/mcp-jive server --help
./bin/mcp-jive dev --help
./bin/mcp-jive tools --help

# Subcommand help
./bin/mcp-jive server start --help
./bin/mcp-jive tools health-check --help
```

## Contributing

When adding new scripts:

1. Place them in the appropriate directory (`scripts/dev/`, `scripts/server/`, etc.)
2. Make them executable: `chmod +x script_name.py`
3. Add them to the unified CLI in `bin/mcp-jive`
4. Update this documentation
5. Add appropriate help text and argument parsing

## Future Enhancements

- Auto-completion for shell environments
- Configuration file validation
- Plugin system for custom tools
- Integration with CI/CD pipelines
- Performance monitoring and metrics